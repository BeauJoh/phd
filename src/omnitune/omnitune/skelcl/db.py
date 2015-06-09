from __future__ import division

import sqlite3 as sql

import labm8 as lab
from labm8 import db
from labm8 import fs
from labm8 import io
from labm8 import math as labmath

import omnitune
from omnitune import llvm

from . import get_user_source
from . import hash_device
from . import hash_kernel
from . import hash_dataset
from . import hash_scenario
from . import hash_params


class Database(db.Database):
    """
    Persistent database store for SkelCL runtime data.

    Tables:
        kernels   Table of kernel attributes.
        devices   Table of device attributes.
        datasets  Table of dataset attributes.
        params    Table of parameter attributes.
        scenarios Table of scenario attributes.
        runtimes  Table of runtime information.
    """

    def __init__(self, path=fs.path(omnitune.LOCAL_DIR, "skelcl.db")):
        """
        Create a new connection to database.

        Arguments:
           path (optional) If set, load database from path. If not, use
               standard system-wide default path.
        """
        super(Database, self).__init__(path)

        # Create tables if needed.
        if self.isempty():
            self.create_tables()

        # Get the database version.
        try:
            # Look up the version in the table.
            query = self.execute("SELECT version from version")
            self.version = query.fetchone()[0]
        except Exception:
            # Base case: This is pre-versioning.
            self.version = 0

    def num_runtimes(self):
        """
        Return the number of runtimes.

        Returns:

            int: Number of rows in runtimes table.
        """
        query = self.execute("SELECT Count(*) FROM runtimes")
        return query.fetchone()[0]

    def merge(self, rhs):
        """
        Merge the contents of the supplied database.

        Arguments:

            rhs (Database): Database instance to merge into this.
        """
        self.attach(rhs.path, "rhs")

        self.execute("INSERT OR IGNORE INTO kernels SELECT * from rhs.kernels")
        self.execute("INSERT OR IGNORE INTO devices SELECT * from rhs.devices")
        self.execute("INSERT OR IGNORE INTO datasets SELECT * from rhs.datasets")
        self.execute("INSERT OR IGNORE INTO scenarios SELECT * from rhs.scenarios")
        self.execute("INSERT OR IGNORE INTO params SELECT * from rhs.params")
        self.execute("INSERT INTO runtimes SELECT * from rhs.runtimes")

        self.detach("rhs")

    def create_tables(self):
        """
        Instantiate the necessary tables.
        """
        # Create table: kernels
        self.create_table("version",
                         (("version",                         "integer"),))
        # Set version.
        self.execute("INSERT INTO version VALUES (2)")

        # Create table: kernels
        self.create_table("kernels",
                         (("id",                              "text primary key"),
                          ("north",                           "integer"),
                          ("south",                           "integer"),
                          ("east",                            "integer"),
                          ("west",                            "integer"),
                          ("max_wg_size",                     "integer"),
                          ("source",                          "text")))

        # Create table: devices
        self.create_table("devices",
                         (("id",                              "text primary key"),
                          ("name",                            "text"),
                          ("count",                           "integer"),
                          ("address_bits",                    "integer"),
                          ("double_fp_config",                "integer"),
                          ("endian_little",                   "integer"),
                          ("execution_capabilities",          "integer"),
                          ("extensions",                      "text"),
                          ("global_mem_cache_size",           "integer"),
                          ("global_mem_cache_type",           "integer"),
                          ("global_mem_cacheline_size",       "integer"),
                          ("global_mem_size",                 "integer"),
                          ("host_unified_memory",             "integer"),
                          ("image2d_max_height",              "integer"),
                          ("image2d_max_width",               "integer"),
                          ("image3d_max_depth",               "integer"),
                          ("image3d_max_height",              "integer"),
                          ("image3d_max_width",               "integer"),
                          ("image_support",                   "integer"),
                          ("local_mem_size",                  "integer"),
                          ("local_mem_type",                  "integer"),
                          ("max_clock_frequency",             "integer"),
                          ("max_compute_units",               "integer"),
                          ("max_constant_args",               "integer"),
                          ("max_constant_buffer_size",        "integer"),
                          ("max_mem_alloc_size",              "integer"),
                          ("max_parameter_size",              "integer"),
                          ("max_read_image_args",             "integer"),
                          ("max_samplers",                    "integer"),
                          ("max_work_group_size",             "integer"),
                          ("max_work_item_dimensions",        "integer"),
                          ("max_work_item_sizes_0",           "integer"),
                          ("max_work_item_sizes_1",           "integer"),
                          ("max_work_item_sizes_2",           "integer"),
                          ("max_write_image_args",            "integer"),
                          ("mem_base_addr_align",             "integer"),
                          ("min_data_type_align_size",        "integer"),
                          ("native_vector_width_char",        "integer"),
                          ("native_vector_width_double",      "integer"),
                          ("native_vector_width_float",       "integer"),
                          ("native_vector_width_half",        "integer"),
                          ("native_vector_width_int",         "integer"),
                          ("native_vector_width_long",        "integer"),
                          ("native_vector_width_short",       "integer"),
                          ("preferred_vector_width_char",     "integer"),
                          ("preferred_vector_width_double",   "integer"),
                          ("preferred_vector_width_float",    "integer"),
                          ("preferred_vector_width_half",     "integer"),
                          ("preferred_vector_width_int",      "integer"),
                          ("preferred_vector_width_long",     "integer"),
                          ("preferred_vector_width_short",    "integer"),
                          ("queue_properties",                "integer"),
                          ("single_fp_config",                "integer"),
                          ("type",                            "integer"),
                          ("vendor",                          "text"),
                          ("vendor_id",                       "text"),
                          ("version",                         "text")))

        # Create table: data
        self.create_table("datasets",
                         (("id",                              "text primary key"),
                          ("width",                           "integer"),
                          ("height",                          "integer"),
                          ("tin",                             "text"),
                          ("tout",                            "text")))

        # Create table: scenarios
        self.create_table("scenarios",
                         (("id",                              "text primary key"),
                          ("host",                            "text"),
                          ("device",                          "text"),
                          ("kernel",                          "text"),
                          ("dataset",                         "text")))

        # Create table: params
        self.create_table("params",
                         (("id",                              "text primary key"),
                          ("wg_c",                            "integer"),
                          ("wg_r",                            "integer")))

        # Create table: runtimes
        self.create_table("runtimes",
                         (("scenario",                        "text"),
                          ("params",                          "text"),
                          ("runtime",                         "real")))

    def device_exists(self, device_id):
        """
        Returns whether there's a "devices" table entry for device.

        Arguments:

            device_id (str): Devices table ID.

        Returns:

            bool: True if row exists, else false.
        """
        query = self.execute("SELECT id FROM devices where id=?", (device_id,))
        return True if query.fetchone() else False

    def add_device(self, devinfo, dev_count):
        """
        Add a new row of device info.

        Arguments:

            deviceinfo (dict of {string:(int|str)}): The device info,
              as returned by opencl.get_devinfo().
            dev_count (int): The number of devices.

        Returns:

            str: The device ID.
        """
        dev_name = devinfo["name"]
        checksum = hash_device(dev_name, dev_count)

        # Quit if there's already an entry for the device.
        if self.device_exists(checksum):
            return checksum

        columns = (
            checksum,
            dev_name,
            dev_count,
            devinfo["address_bits"],
            devinfo["double_fp_config"],
            devinfo["endian_little"],
            devinfo["execution_capabilities"],
            devinfo["extensions"],
            devinfo["global_mem_cache_size"],
            devinfo["global_mem_cache_type"],
            devinfo["global_mem_cacheline_size"],
            devinfo["global_mem_size"],
            devinfo["host_unified_memory"],
            devinfo["image2d_max_height"],
            devinfo["image2d_max_width"],
            devinfo["image3d_max_depth"],
            devinfo["image3d_max_height"],
            devinfo["image3d_max_width"],
            devinfo["image_support"],
            devinfo["local_mem_size"],
            devinfo["local_mem_type"],
            devinfo["max_clock_frequency"],
            devinfo["max_compute_units"],
            devinfo["max_constant_args"],
            devinfo["max_constant_buffer_size"],
            devinfo["max_mem_alloc_size"],
            devinfo["max_parameter_size"],
            devinfo["max_read_image_args"],
            devinfo["max_samplers"],
            devinfo["max_work_group_size"],
            devinfo["max_work_item_dimensions"],
            devinfo["max_work_item_sizes_0"],
            devinfo["max_work_item_sizes_1"],
            devinfo["max_work_item_sizes_2"],
            devinfo["max_write_image_args"],
            devinfo["mem_base_addr_align"],
            devinfo["min_data_type_align_size"],
            devinfo["native_vector_width_char"],
            devinfo["native_vector_width_double"],
            devinfo["native_vector_width_float"],
            devinfo["native_vector_width_half"],
            devinfo["native_vector_width_int"],
            devinfo["native_vector_width_long"],
            devinfo["native_vector_width_short"],
            devinfo["preferred_vector_width_char"],
            devinfo["preferred_vector_width_double"],
            devinfo["preferred_vector_width_float"],
            devinfo["preferred_vector_width_half"],
            devinfo["preferred_vector_width_int"],
            devinfo["preferred_vector_width_long"],
            devinfo["preferred_vector_width_short"],
            devinfo["queue_properties"],
            devinfo["single_fp_config"],
            devinfo["type"],
            devinfo["vendor"],
            devinfo["vendor_id"],
            devinfo["version"]
        )

        placeholders = ",".join(["?"] * len(columns))
        self.execute("INSERT INTO devices VALUES (" + placeholders + ")",
                     columns)

        return checksum

    def kernel_exists(self, kernel_id):
        """
        Returns whether there's a "kernels" table entry for kernel.

        Arguments:

            kernel_id (str): Kernel table ID.

        Returns:

            bool: True if row exists, else false.
        """
        query = self.execute("SELECT id FROM kernels where id=?", (kernel_id,))
        return True if query.fetchone() else False

    def add_kernel(self, north, south, east, west, max_wg_size, source):
        """
        Add a new row of kernel info.

        Arguments:

            north (int): The stencil shape north direction.
            south (int): The stencil shape south direction.
            east (int): The stencil shape east direction.
            west (int): The stencil shape west direction.
            max_wg_size (int): The maximum kernel workgroup size.
            source (str): The stencil kernel source code.

        Returns:

            str: The kernel ID.
        """
        checksum = hash_kernel(north, south, east, west, max_wg_size, source)

        # Quit if there's already an entry for the kernel.
        if self.kernel_exists(checksum):
            return checksum

        user_source = get_user_source(source)

        columns = (
            checksum,
            north,
            south,
            east,
            west,
            max_wg_size,
            user_source
        )

        self.execute("INSERT INTO kernels VALUES (?,?,?,?,?,?,?)", columns)
        return checksum

    def dataset_exists(self, dataset_id):
        """
        Returns whether there's a "datasets" table entry for dataset.

        Arguments:

            dataset_id (str): Dataset table ID.

        Returns:

            bool: True if row exists, else false.
        """
        query = self.execute("SELECT id FROM datasets where id=?",
                             (dataset_id,))
        return True if query.fetchone() else False

    def add_dataset(self, width, height, tin, tout):
        """
        Add a new row of dataset info.

        Arguments:

            data_width (int): The number of columns of data.
            data_height (int): The number of rows of data.
            type_in (str): The input data type.
            type_out (str): The output data type.

        Returns:

            str: The dataset ID.
        """
        checksum = hash_dataset(width, height, tin, tout)

        # Quit if there's already an entry for the kernel.
        if self.dataset_exists(checksum):
            return checksum

        columns = (
            checksum,
            width,
            height,
            tin,
            tout
        )

        self.execute("INSERT INTO datasets VALUES (?,?,?,?,?)", columns)
        return checksum

    def scenario_exists(self, scenario_id):
        """
        Returns whether there's a "scenarios" table entry for scenario.

        Arguments:

            scenario_id (str): Scenario table ID.

        Returns:

            bool: True if row exists, else false.
        """
        query = self.execute("SELECT id FROM scenarios where id=?",
                             (scenario_id,))
        return True if query.fetchone() else False

    def add_scenario(self, host, device, kernel, dataset):
        """
        Add a new row of scenario info.

        Arguments:

            host (str): The system hostname
            device (str): The device ID
            kernel (str): The kernel ID
            dataset (str): The dataset ID

        Returns:

            str: The scenario ID.
        """
        checksum = hash_scenario(host, device, kernel, dataset)

        # Quit if there's already an entry for the kernel.
        if self.scenario_exists(checksum):
            return checksum

        columns = (
            checksum,
            host,
            device,
            kernel,
            dataset
        )

        self.execute("INSERT INTO scenarios VALUES (?,?,?,?,?)", columns)
        return checksum

    def params_exists(self, params_id):
        """
        Returns whether there's a "params" table entry for params.

        Arguments:

            params_id (str): Parameters table ID.

        Returns:

            bool: True if row exists, else false.
        """
        query = self.execute("SELECT id FROM params where id=?",
                             (params_id,))
        return True if query.fetchone() else False

    def add_params(self, wg_c, wg_r):
        """
        Add a new row of params info.

        Arguments:

            wg_c (int): The workgroup size (columns)
            wg_r (int): The workgroup size (rows)

        Returns:

            str: The params ID.
        """
        checksum = hash_params(wg_c, wg_r)

        # Quit if there's already an entry for the kernel.
        if self.params_exists(checksum):
            return checksum

        columns = (
            checksum,
            wg_c,
            wg_r
        )

        self.execute("INSERT INTO params VALUES (?,?,?)", columns)
        return checksum

    def add_runtime(self, scenario, params, runtime):
        """
        Add a new measured experimental runtime.
        """
        self.execute("INSERT INTO runtimes VALUES (?,?,?)",
                     (scenario, params, runtime))

    def lookup_runtimes_count(self, scenario, params):
        """
        Return the number of runtimes for a particular scenario + params.
        """
        query = self.execute("SELECT Count(*) FROM runtimes WHERE "
                             "scenario=? AND params=?", (scenario, params))
        return query.fetchone()[0]


    def create_samples_table(self):
        self.create_table("samples", SAMPLES_TABLE)

        query_keys = [x[0] for x in RUNTIMES_TABLE[:-1]]
        query = self.execute("SELECT DISTINCT " + ",".join(query_keys) +
                             " FROM runtimes")

        for row in query:
            where_c = ["{key}=?".format(key=key) for key in query_keys]
            where = " AND ".join(where_c)

            runtimes_query = self.execute("SELECT runtime from runtimes WHERE "
                                          + where, row)
            runtimes = [x[0] for x in runtimes_query]
            sample_count = len(runtimes)
            runtime = labmath.mean(runtimes)

            samples_values = (
                row[0],   # host
                row[1],   # device
                row[2],   # dev_count
                row[3],   # kernel
                row[8],   # data_width
                row[9],   # data_height
                row[11],  # wg_c
                row[12],  # wg_r
                sample_count,
                runtime
            )
            io.debug(*samples_values)
            self.insert("INSERT INTO samples VALUES (?,?,?,?,?,?,?,?)",
                        samples_values)

    def lookup_best_workgroup_size(self, scenario):
        """
        Return the best workgroup size for a given scenario.

        Returns the workgroup size which, for a given scenario,
        resulted in the lowest mean runtime.

        Arguments:

            scenario (str): The scenario ID to lookup.

        Returns:

            tuple of ints: In the form (wg_c,wg_r).
        """
        cmd = ("SELECT wg_c,wg_r FROM params WHERE id=("
               "SELECT params from runtimes WHERE scenario=? AND "
               "runtime=(SELECT MIN(runtime) FROM runtimes WHERE SCENARIO=?))")
        args = (scenario,scenario)
        io.info(cmd)
        query = self.execute(cmd, args)

        return query.fetchone()


CREATE_FEATURES_RUNTIME_STATS_TABLE = """
CREATE TABLE IF NOT EXISTS features_runtime_stats (
  data_width integer,
  data_height integer,
  data_tin text,
  data_tout text,
  kern_north integer,
  kern_south integer,
  kern_east integer,
  kern_west integer,
  kern_max_wg_size integer,
  kern_instruction_count integer,
  kern_ratio_AShr_insts real,
  kern_ratio_Add_insts real,
  kern_ratio_Alloca_insts real,
  kern_ratio_And_insts real,
  kern_ratio_Br_insts real,
  kern_ratio_Call_insts real,
  kern_ratio_FAdd_insts real,
  kern_ratio_FCmp_insts real,
  kern_ratio_FDiv_insts real,
  kern_ratio_FMul_insts real,
  kern_ratio_FPExt_insts real,
  kern_ratio_FPToSI_insts real,
  kern_ratio_FSub_insts real,
  kern_ratio_GetElementPtr_insts real,
  kern_ratio_ICmp_insts real,
  kern_ratio_InsertValue_insts real,
  kern_ratio_Load_insts real,
  kern_ratio_Mul_insts real,
  kern_ratio_Or_insts real,
  kern_ratio_PHI_insts real,
  kern_ratio_Ret_insts real,
  kern_ratio_SDiv_insts real,
  kern_ratio_SExt_insts real,
  kern_ratio_SIToFP_insts real,
  kern_ratio_SRem_insts real,
  kern_ratio_Select_insts real,
  kern_ratio_Shl_insts real,
  kern_ratio_Store_insts real,
  kern_ratio_Sub_insts real,
  kern_ratio_Trunc_insts real,
  kern_ratio_UDiv_insts real,
  kern_ratio_Xor_insts real,
  kern_ratio_ZExt_insts real,
  kern_ratio_basic_blocks real,
  kern_ratio_memory_instructions real,
  kern_ratio_non_external_functions real,
  dev_count integer,
  dev_address_bits integer,
  dev_double_fp_config integer,
  dev_endian_little integer,
  dev_execution_capabilities integer,
  dev_extensions text,
  dev_global_mem_cache_size integer,
  dev_global_mem_cache_type integer,
  dev_global_mem_cacheline_size integer,
  dev_global_mem_size integer,
  dev_host_unified_memory integer,
  dev_image2d_max_height integer,
  dev_image2d_max_width integer,
  dev_image3d_max_depth integer,
  dev_image3d_max_height integer,
  dev_image3d_max_width integer,
  dev_image_support integer,
  dev_local_mem_size integer,
  dev_local_mem_type integer,
  dev_max_clock_frequency integer,
  dev_max_compute_units integer,
  dev_max_constant_args integer,
  dev_max_constant_buffer_size integer,
  dev_max_mem_alloc_size integer,
  dev_max_parameter_size integer,
  dev_max_read_image_args integer,
  dev_max_samplers integer,
  dev_max_work_group_size integer,
  dev_max_work_item_dimensions integer,
  dev_max_work_item_sizes_0 integer,
  dev_max_work_item_sizes_1 integer,
  dev_max_work_item_sizes_2 integer,
  dev_max_write_image_args integer,
  dev_mem_base_addr_align integer,
  dev_min_data_type_align_size integer,
  dev_native_vector_width_char integer,
  dev_native_vector_width_double integer,
  dev_native_vector_width_float integer,
  dev_native_vector_width_half integer,
  dev_native_vector_width_int integer,
  dev_native_vector_width_long integer,
  dev_native_vector_width_short integer,
  dev_preferred_vector_width_char integer,
  dev_preferred_vector_width_double integer,
  dev_preferred_vector_width_float integer,
  dev_preferred_vector_width_half integer,
  dev_preferred_vector_width_int integer,
  dev_preferred_vector_width_long integer,
  dev_preferred_vector_width_short integer,
  dev_queue_properties integer,
  dev_single_fp_config integer,
  dev_type integer,
  dev_vendor text,
  dev_vendor_id text,
  dev_version text,
  wgsize text,
  runtime real
)"""


POPULATE_FEATURES_RUNTIME_STATS_TABLE = """
INSERT INTO features_runtime_stats SELECT
  width                          as  data_width,
  height                         as  data_height,
  tin                            as  data_tin,
  tout                           as  data_tout,
  north                          as  kern_north,
  south                          as  kern_south,
  east                           as  kern_east,
  west                           as  kern_west,
  instruction_count              as  kern_instruction_count,
  ratio_AShr_insts               as  kern_ratio_AShr_insts,
  ratio_Add_insts                as  kern_ratio_Add_insts,
  ratio_Alloca_insts             as  kern_ratio_Alloca_insts,
  ratio_And_insts                as  kern_ratio_And_insts,
  ratio_Br_insts                 as  kern_ratio_Br_insts,
  ratio_Call_insts               as  kern_ratio_Call_insts,
  ratio_FAdd_insts               as  kern_ratio_FAdd_insts,
  ratio_FCmp_insts               as  kern_ratio_FCmp_insts,
  ratio_FDiv_insts               as  kern_ratio_FDiv_insts,
  ratio_FMul_insts               as  kern_ratio_FMul_insts,
  ratio_FPExt_insts              as  kern_ratio_FPExt_insts,
  ratio_FPToSI_insts             as  kern_ratio_FPToSI_insts,
  ratio_FSub_insts               as  kern_ratio_FSub_insts,
  ratio_GetElementPtr_insts      as  kern_ratio_GetElementPtr_insts,
  ratio_ICmp_insts               as  kern_ratio_ICmp_insts,
  ratio_InsertValue_insts        as  kern_ratio_InsertValue_insts,
  ratio_Load_insts               as  kern_ratio_Load_insts,
  ratio_Mul_insts                as  kern_ratio_Mul_insts,
  ratio_Or_insts                 as  kern_ratio_Or_insts,
  ratio_PHI_insts                as  kern_ratio_PHI_insts,
  ratio_Ret_insts                as  kern_ratio_Ret_insts,
  ratio_SDiv_insts               as  kern_ratio_SDiv_insts,
  ratio_SExt_insts               as  kern_ratio_SExt_insts,
  ratio_SIToFP_insts             as  kern_ratio_SIToFP_insts,
  ratio_SRem_insts               as  kern_ratio_SRem_insts,
  ratio_Select_insts             as  kern_ratio_Select_insts,
  ratio_Shl_insts                as  kern_ratio_Shl_insts,
  ratio_Store_insts              as  kern_ratio_Store_insts,
  ratio_Sub_insts                as  kern_ratio_Sub_insts,
  ratio_Trunc_insts              as  kern_ratio_Trunc_insts,
  ratio_UDiv_insts               as  kern_ratio_UDiv_insts,
  ratio_Xor_insts                as  kern_ratio_Xor_insts,
  ratio_ZExt_insts               as  kern_ratio_ZExt_insts,
  ratio_basic_blocks             as  kern_ratio_basic_blocks,
  ratio_memory_instructions      as  kern_ratio_memory_instructions,
  ratio_non_external_functions   as  kern_ratio_non_external_functions,
  max_wg_size                    as  kern_max_wg_size,
  count                          as  dev_count,
  address_bits                   as  dev_address_bits,
  double_fp_config               as  dev_double_fp_config,
  endian_little                  as  dev_endian_little,
  execution_capabilities         as  dev_execution_capabilities,
  extensions                     as  dev_extensions,
  global_mem_cache_size          as  dev_global_mem_cache_size,
  global_mem_cache_type          as  dev_global_mem_cache_type,
  global_mem_cacheline_size      as  dev_global_mem_cacheline_size,
  global_mem_size                as  dev_global_mem_size,
  host_unified_memory            as  dev_host_unified_memory,
  image2d_max_height             as  dev_image2d_max_height,
  image2d_max_width              as  dev_image2d_max_width,
  image3d_max_depth              as  dev_image3d_max_depth,
  image3d_max_height             as  dev_image3d_max_height,
  image3d_max_width              as  dev_image3d_max_width,
  image_support                  as  dev_image_support,
  local_mem_size                 as  dev_local_mem_size,
  local_mem_type                 as  dev_local_mem_type,
  max_clock_frequency            as  dev_max_clock_frequency,
  max_compute_units              as  dev_max_compute_units,
  max_constant_args              as  dev_max_constant_args,
  max_constant_buffer_size       as  dev_max_constant_buffer_size,
  max_mem_alloc_size             as  dev_max_mem_alloc_size,
  max_parameter_size             as  dev_max_parameter_size,
  max_read_image_args            as  dev_max_read_image_args,
  max_samplers                   as  dev_max_samplers,
  max_work_group_size            as  dev_max_work_group_size,
  max_work_item_dimensions       as  dev_max_work_item_dimensions,
  max_work_item_sizes_0          as  dev_max_work_item_sizes_0,
  max_work_item_sizes_1          as  dev_max_work_item_sizes_1,
  max_work_item_sizes_2          as  dev_max_work_item_sizes_2,
  max_write_image_args           as  dev_max_write_image_args,
  mem_base_addr_align            as  dev_mem_base_addr_align,
  min_data_type_align_size       as  dev_min_data_type_align_size,
  native_vector_width_char       as  dev_native_vector_width_char,
  native_vector_width_double     as  dev_native_vector_width_double,
  native_vector_width_float      as  dev_native_vector_width_float,
  native_vector_width_half       as  dev_native_vector_width_half,
  native_vector_width_int        as  dev_native_vector_width_int,
  native_vector_width_long       as  dev_native_vector_width_long,
  native_vector_width_short      as  dev_native_vector_width_short,
  preferred_vector_width_char    as  dev_preferred_vector_width_char,
  preferred_vector_width_double  as  dev_preferred_vector_width_double,
  preferred_vector_width_float   as  dev_preferred_vector_width_float,
  preferred_vector_width_half    as  dev_preferred_vector_width_half,
  preferred_vector_width_int     as  dev_preferred_vector_width_int,
  preferred_vector_width_long    as  dev_preferred_vector_width_long,
  preferred_vector_width_short   as  dev_preferred_vector_width_short,
  queue_properties               as  dev_queue_properties,
  single_fp_config               as  dev_single_fp_config,
  type                           as  dev_type,
  vendor                         as  dev_vendor,
  vendor_id                      as  dev_vendor_id,
  version                        as  dev_version,
  params                         as  wgsize,
  mean                           as  runtime
FROM (
    SELECT * FROM (
        SELECT * FROM (
            SELECT * FROM runtime_stats
            LEFT JOIN scenarios ON runtime_stats.scenario=scenarios.id
        ) LEFT JOIN dataset_features ON dataset=dataset_features.id
    ) LEFT JOIN kernel_features ON kernel=kernel_features.id
) LEFT JOIN device_features ON device=device_features.id"""


CREATE_FEATURES_ORACLE_PARAMS_TABLE = """
CREATE TABLE IF NOT EXISTS features_oracle_params (
  data_width integer,
  data_height integer,
  data_tin text,
  data_tout text,
  kern_north integer,
  kern_south integer,
  kern_east integer,
  kern_west integer,
  kern_max_wg_size integer,
  kern_instruction_count integer,
  kern_ratio_AShr_insts real,
  kern_ratio_Add_insts real,
  kern_ratio_Alloca_insts real,
  kern_ratio_And_insts real,
  kern_ratio_Br_insts real,
  kern_ratio_Call_insts real,
  kern_ratio_FAdd_insts real,
  kern_ratio_FCmp_insts real,
  kern_ratio_FDiv_insts real,
  kern_ratio_FMul_insts real,
  kern_ratio_FPExt_insts real,
  kern_ratio_FPToSI_insts real,
  kern_ratio_FSub_insts real,
  kern_ratio_GetElementPtr_insts real,
  kern_ratio_ICmp_insts real,
  kern_ratio_InsertValue_insts real,
  kern_ratio_Load_insts real,
  kern_ratio_Mul_insts real,
  kern_ratio_Or_insts real,
  kern_ratio_PHI_insts real,
  kern_ratio_Ret_insts real,
  kern_ratio_SDiv_insts real,
  kern_ratio_SExt_insts real,
  kern_ratio_SIToFP_insts real,
  kern_ratio_SRem_insts real,
  kern_ratio_Select_insts real,
  kern_ratio_Shl_insts real,
  kern_ratio_Store_insts real,
  kern_ratio_Sub_insts real,
  kern_ratio_Trunc_insts real,
  kern_ratio_UDiv_insts real,
  kern_ratio_Xor_insts real,
  kern_ratio_ZExt_insts real,
  kern_ratio_basic_blocks real,
  kern_ratio_memory_instructions real,
  kern_ratio_non_external_functions real,
  dev_count integer,
  dev_address_bits integer,
  dev_double_fp_config integer,
  dev_endian_little integer,
  dev_execution_capabilities integer,
  dev_extensions text,
  dev_global_mem_cache_size integer,
  dev_global_mem_cache_type integer,
  dev_global_mem_cacheline_size integer,
  dev_global_mem_size integer,
  dev_host_unified_memory integer,
  dev_image2d_max_height integer,
  dev_image2d_max_width integer,
  dev_image3d_max_depth integer,
  dev_image3d_max_height integer,
  dev_image3d_max_width integer,
  dev_image_support integer,
  dev_local_mem_size integer,
  dev_local_mem_type integer,
  dev_max_clock_frequency integer,
  dev_max_compute_units integer,
  dev_max_constant_args integer,
  dev_max_constant_buffer_size integer,
  dev_max_mem_alloc_size integer,
  dev_max_parameter_size integer,
  dev_max_read_image_args integer,
  dev_max_samplers integer,
  dev_max_work_group_size integer,
  dev_max_work_item_dimensions integer,
  dev_max_work_item_sizes_0 integer,
  dev_max_work_item_sizes_1 integer,
  dev_max_work_item_sizes_2 integer,
  dev_max_write_image_args integer,
  dev_mem_base_addr_align integer,
  dev_min_data_type_align_size integer,
  dev_native_vector_width_char integer,
  dev_native_vector_width_double integer,
  dev_native_vector_width_float integer,
  dev_native_vector_width_half integer,
  dev_native_vector_width_int integer,
  dev_native_vector_width_long integer,
  dev_native_vector_width_short integer,
  dev_preferred_vector_width_char integer,
  dev_preferred_vector_width_double integer,
  dev_preferred_vector_width_float integer,
  dev_preferred_vector_width_half integer,
  dev_preferred_vector_width_int integer,
  dev_preferred_vector_width_long integer,
  dev_preferred_vector_width_short integer,
  dev_queue_properties integer,
  dev_single_fp_config integer,
  dev_type integer,
  dev_vendor text,
  dev_vendor_id text,
  dev_version text,
  wgsize text
)"""


POPULATE_FEATURES_ORACLE_PARAMS_TABLE = """
INSERT INTO features_oracle_params SELECT
  width                          as  data_width,
  height                         as  data_height,
  tin                            as  data_tin,
  tout                           as  data_tout,
  north                          as  kern_north,
  south                          as  kern_south,
  east                           as  kern_east,
  west                           as  kern_west,
  instruction_count              as  kern_instruction_count,
  ratio_AShr_insts               as  kern_ratio_AShr_insts,
  ratio_Add_insts                as  kern_ratio_Add_insts,
  ratio_Alloca_insts             as  kern_ratio_Alloca_insts,
  ratio_And_insts                as  kern_ratio_And_insts,
  ratio_Br_insts                 as  kern_ratio_Br_insts,
  ratio_Call_insts               as  kern_ratio_Call_insts,
  ratio_FAdd_insts               as  kern_ratio_FAdd_insts,
  ratio_FCmp_insts               as  kern_ratio_FCmp_insts,
  ratio_FDiv_insts               as  kern_ratio_FDiv_insts,
  ratio_FMul_insts               as  kern_ratio_FMul_insts,
  ratio_FPExt_insts              as  kern_ratio_FPExt_insts,
  ratio_FPToSI_insts             as  kern_ratio_FPToSI_insts,
  ratio_FSub_insts               as  kern_ratio_FSub_insts,
  ratio_GetElementPtr_insts      as  kern_ratio_GetElementPtr_insts,
  ratio_ICmp_insts               as  kern_ratio_ICmp_insts,
  ratio_InsertValue_insts        as  kern_ratio_InsertValue_insts,
  ratio_Load_insts               as  kern_ratio_Load_insts,
  ratio_Mul_insts                as  kern_ratio_Mul_insts,
  ratio_Or_insts                 as  kern_ratio_Or_insts,
  ratio_PHI_insts                as  kern_ratio_PHI_insts,
  ratio_Ret_insts                as  kern_ratio_Ret_insts,
  ratio_SDiv_insts               as  kern_ratio_SDiv_insts,
  ratio_SExt_insts               as  kern_ratio_SExt_insts,
  ratio_SIToFP_insts             as  kern_ratio_SIToFP_insts,
  ratio_SRem_insts               as  kern_ratio_SRem_insts,
  ratio_Select_insts             as  kern_ratio_Select_insts,
  ratio_Shl_insts                as  kern_ratio_Shl_insts,
  ratio_Store_insts              as  kern_ratio_Store_insts,
  ratio_Sub_insts                as  kern_ratio_Sub_insts,
  ratio_Trunc_insts              as  kern_ratio_Trunc_insts,
  ratio_UDiv_insts               as  kern_ratio_UDiv_insts,
  ratio_Xor_insts                as  kern_ratio_Xor_insts,
  ratio_ZExt_insts               as  kern_ratio_ZExt_insts,
  ratio_basic_blocks             as  kern_ratio_basic_blocks,
  ratio_memory_instructions      as  kern_ratio_memory_instructions,
  ratio_non_external_functions   as  kern_ratio_non_external_functions,
  max_wg_size                    as  kern_max_wg_size,
  count                          as  dev_count,
  address_bits                   as  dev_address_bits,
  double_fp_config               as  dev_double_fp_config,
  endian_little                  as  dev_endian_little,
  execution_capabilities         as  dev_execution_capabilities,
  extensions                     as  dev_extensions,
  global_mem_cache_size          as  dev_global_mem_cache_size,
  global_mem_cache_type          as  dev_global_mem_cache_type,
  global_mem_cacheline_size      as  dev_global_mem_cacheline_size,
  global_mem_size                as  dev_global_mem_size,
  host_unified_memory            as  dev_host_unified_memory,
  image2d_max_height             as  dev_image2d_max_height,
  image2d_max_width              as  dev_image2d_max_width,
  image3d_max_depth              as  dev_image3d_max_depth,
  image3d_max_height             as  dev_image3d_max_height,
  image3d_max_width              as  dev_image3d_max_width,
  image_support                  as  dev_image_support,
  local_mem_size                 as  dev_local_mem_size,
  local_mem_type                 as  dev_local_mem_type,
  max_clock_frequency            as  dev_max_clock_frequency,
  max_compute_units              as  dev_max_compute_units,
  max_constant_args              as  dev_max_constant_args,
  max_constant_buffer_size       as  dev_max_constant_buffer_size,
  max_mem_alloc_size             as  dev_max_mem_alloc_size,
  max_parameter_size             as  dev_max_parameter_size,
  max_read_image_args            as  dev_max_read_image_args,
  max_samplers                   as  dev_max_samplers,
  max_work_group_size            as  dev_max_work_group_size,
  max_work_item_dimensions       as  dev_max_work_item_dimensions,
  max_work_item_sizes_0          as  dev_max_work_item_sizes_0,
  max_work_item_sizes_1          as  dev_max_work_item_sizes_1,
  max_work_item_sizes_2          as  dev_max_work_item_sizes_2,
  max_write_image_args           as  dev_max_write_image_args,
  mem_base_addr_align            as  dev_mem_base_addr_align,
  min_data_type_align_size       as  dev_min_data_type_align_size,
  native_vector_width_char       as  dev_native_vector_width_char,
  native_vector_width_double     as  dev_native_vector_width_double,
  native_vector_width_float      as  dev_native_vector_width_float,
  native_vector_width_half       as  dev_native_vector_width_half,
  native_vector_width_int        as  dev_native_vector_width_int,
  native_vector_width_long       as  dev_native_vector_width_long,
  native_vector_width_short      as  dev_native_vector_width_short,
  preferred_vector_width_char    as  dev_preferred_vector_width_char,
  preferred_vector_width_double  as  dev_preferred_vector_width_double,
  preferred_vector_width_float   as  dev_preferred_vector_width_float,
  preferred_vector_width_half    as  dev_preferred_vector_width_half,
  preferred_vector_width_int     as  dev_preferred_vector_width_int,
  preferred_vector_width_long    as  dev_preferred_vector_width_long,
  preferred_vector_width_short   as  dev_preferred_vector_width_short,
  queue_properties               as  dev_queue_properties,
  single_fp_config               as  dev_single_fp_config,
  type                           as  dev_type,
  vendor                         as  dev_vendor,
  vendor_id                      as  dev_vendor_id,
  version                        as  dev_version,
  params                         as  wgsize
FROM (
    SELECT * FROM (
        SELECT * FROM (
            SELECT * FROM oracle_params
            LEFT JOIN scenarios ON oracle_params.scenario=scenarios.id
        ) LEFT JOIN dataset_features ON dataset=dataset_features.id
    ) LEFT JOIN kernel_features ON kernel=kernel_features.id
) LEFT JOIN device_features ON device=device_features.id"""


class MLDatabase(Database):
    """
    Persistent database store for SkelCL training data.

    Extends the base class Database with additional tables.

    Tables (in addition to those of base class Database):
        kernel_features  Table of kernel features.
        device_features  Table of device features.
        dataset_features Table of dataset features.
        runtime_stats    Table of (scenario,params,runtime) observations.
        oracle_params    Table of (scenario,params,num_samples,mean_runtime)
                         tuples, where params is the params which
                         provided the lowest runtime.
    """

    def __init__(self, path=fs.path(omnitune.LOCAL_DIR, "training.db")):
        """
        Create a new connection to database.

        Arguments:
            path (str, optional): If set, load database from path. If not, use
              standard system-wide path.
        """
        super(Database, self).__init__(path)


    def create_tables(self):
        # Create table: kernel_features
        self.create_table("kernel_features",
                          (("id",                              "text primary key"),
                           ("north",                           "integer"),
                           ("south",                           "integer"),
                           ("east",                            "integer"),
                           ("west",                            "integer"),
                           ("max_wg_size",                     "integer"),
                           ("instruction_count",               "integer"),
                           ("ratio_AShr_insts",                "real"),
                           ("ratio_Add_insts",                 "real"),
                           ("ratio_Alloca_insts",              "real"),
                           ("ratio_And_insts",                 "real"),
                           ("ratio_Br_insts",                  "real"),
                           ("ratio_Call_insts",                "real"),
                           ("ratio_FAdd_insts",                "real"),
                           ("ratio_FCmp_insts",                "real"),
                           ("ratio_FDiv_insts",                "real"),
                           ("ratio_FMul_insts",                "real"),
                           ("ratio_FPExt_insts",               "real"),
                           ("ratio_FPToSI_insts",              "real"),
                           ("ratio_FSub_insts",                "real"),
                           ("ratio_GetElementPtr_insts",       "real"),
                           ("ratio_ICmp_insts",                "real"),
                           ("ratio_InsertValue_insts",         "real"),
                           ("ratio_Load_insts",                "real"),
                           ("ratio_Mul_insts",                 "real"),
                           ("ratio_Or_insts",                  "real"),
                           ("ratio_PHI_insts",                 "real"),
                           ("ratio_Ret_insts",                 "real"),
                           ("ratio_SDiv_insts",                "real"),
                           ("ratio_SExt_insts",                "real"),
                           ("ratio_SIToFP_insts",              "real"),
                           ("ratio_SRem_insts",                "real"),
                           ("ratio_Select_insts",              "real"),
                           ("ratio_Shl_insts",                 "real"),
                           ("ratio_Store_insts",               "real"),
                           ("ratio_Sub_insts",                 "real"),
                           ("ratio_Trunc_insts",               "real"),
                           ("ratio_UDiv_insts",                "real"),
                           ("ratio_Xor_insts",                 "real"),
                           ("ratio_ZExt_insts",                "real"),
                           ("ratio_basic_blocks",              "real"),
                           ("ratio_memory_instructions",       "real"),
                           ("ratio_non_external_functions",    "real")))

        # Create table: device_features
        self.create_table("device_features",
                          (("id",                              "text primary key"),
                           ("name",                            "text"),
                           ("count",                           "integer"),
                           ("address_bits",                    "integer"),
                           ("double_fp_config",                "integer"),
                           ("endian_little",                   "integer"),
                           ("execution_capabilities",          "integer"),
                           ("extensions",                      "text"),
                           ("global_mem_cache_size",           "integer"),
                           ("global_mem_cache_type",           "integer"),
                           ("global_mem_cacheline_size",       "integer"),
                           ("global_mem_size",                 "integer"),
                           ("host_unified_memory",             "integer"),
                           ("image2d_max_height",              "integer"),
                           ("image2d_max_width",               "integer"),
                           ("image3d_max_depth",               "integer"),
                           ("image3d_max_height",              "integer"),
                           ("image3d_max_width",               "integer"),
                           ("image_support",                   "integer"),
                           ("local_mem_size",                  "integer"),
                           ("local_mem_type",                  "integer"),
                           ("max_clock_frequency",             "integer"),
                           ("max_compute_units",               "integer"),
                           ("max_constant_args",               "integer"),
                           ("max_constant_buffer_size",        "integer"),
                           ("max_mem_alloc_size",              "integer"),
                           ("max_parameter_size",              "integer"),
                           ("max_read_image_args",             "integer"),
                           ("max_samplers",                    "integer"),
                           ("max_work_group_size",             "integer"),
                           ("max_work_item_dimensions",        "integer"),
                           ("max_work_item_sizes_0",           "integer"),
                           ("max_work_item_sizes_1",           "integer"),
                           ("max_work_item_sizes_2",           "integer"),
                           ("max_write_image_args",            "integer"),
                           ("mem_base_addr_align",             "integer"),
                           ("min_data_type_align_size",        "integer"),
                           ("native_vector_width_char",        "integer"),
                           ("native_vector_width_double",      "integer"),
                           ("native_vector_width_float",       "integer"),
                           ("native_vector_width_half",        "integer"),
                           ("native_vector_width_int",         "integer"),
                           ("native_vector_width_long",        "integer"),
                           ("native_vector_width_short",       "integer"),
                           ("preferred_vector_width_char",     "integer"),
                           ("preferred_vector_width_double",   "integer"),
                           ("preferred_vector_width_float",    "integer"),
                           ("preferred_vector_width_half",     "integer"),
                           ("preferred_vector_width_int",      "integer"),
                           ("preferred_vector_width_long",     "integer"),
                           ("preferred_vector_width_short",    "integer"),
                           ("queue_properties",                "integer"),
                           ("single_fp_config",                "integer"),
                           ("type",                            "integer"),
                           ("vendor",                          "text"),
                           ("vendor_id",                       "text"),
                           ("version",                         "text")))

        self.create_table("dataset_features",
                          (("id",                              "text primary key"),
                           ("width",                           "integer"),
                           ("height",                          "integer"),
                           ("tin",                             "text"),
                           ("tout",                            "text")))

        self.create_table("runtime_stats",
                          (("scenario",                        "text"),
                           ("params",                          "text"),
                           ("num_samples",                     "integer"),
                           ("min",                             "real"),
                           ("mean",                            "real"),
                           ("max",                             "real")))

        self.create_table("oracle_params",
                          (("scenario",                        "text primary key"),
                           ("params",                          "text"),
                           ("num_samples",                     "integer"),
                           ("mean_runtime",                    "real")))

        self.execute(CREATE_FEATURES_RUNTIME_STATS_TABLE)
        self.execute(CREATE_FEATURES_ORACLE_PARAMS_TABLE)

    def populate_kernel_features_table(self):
        """
        Derive kernel features from "kernels" table.
        """
        for row in self.execute("SELECT * FROM kernels"):
            source = row[6]
            bitcode = llvm.bitcode(source)
            instcounts = llvm.instcounts(bitcode)
            ratios = llvm.instcounts2ratios(instcounts)
            features = (
                row[0], # id
                row[1], # north
                row[2], # south
                row[3], # east
                row[4], # west
                row[5], # max_wg_size
                ratios.get("instruction_count", 0),           # instruction_count
                ratios.get("ratio AShr insts", 0),            # ratio_AShr_insts
                ratios.get("ratio Add insts", 0),             # ratio_Add_insts
                ratios.get("ratio Alloca insts", 0),          # ratio_Alloca_insts
                ratios.get("ratio And insts", 0),             # ratio_And_insts
                ratios.get("ratio Br insts", 0),              # ratio_Br_insts
                ratios.get("ratio Call insts", 0),            # ratio_Call_insts
                ratios.get("ratio FAdd insts", 0),            # ratio_FAdd_insts
                ratios.get("ratio FCmp insts", 0),            # ratio_FCmp_insts
                ratios.get("ratio FDiv insts", 0),            # ratio_FDiv_insts
                ratios.get("ratio FMul insts", 0),            # ratio_FMul_insts
                ratios.get("ratio FPExt insts", 0),           # ratio_FPExt_insts
                ratios.get("ratio FPToSI insts", 0),          # ratio_FPToSI_insts
                ratios.get("ratio FSub insts", 0),            # ratio_FSub_insts
                ratios.get("ratio GetElementPtr insts", 0),   # ratio_GetElementPtr_insts
                ratios.get("ratio ICmp insts", 0),            # ratio_ICmp_insts
                ratios.get("ratio InsertValue insts", 0),     # ratio_InsertValue_insts
                ratios.get("ratio Load insts", 0),            # ratio_Load_insts
                ratios.get("ratio Mul insts", 0),             # ratio_Mul_insts
                ratios.get("ratio Or insts", 0),              # ratio_Or_insts
                ratios.get("ratio PHI insts", 0),             # ratio_PHI_insts
                ratios.get("ratio Ret insts", 0),             # ratio_Ret_insts
                ratios.get("ratio SDiv insts", 0),            # ratio_SDiv_insts
                ratios.get("ratio SExt insts", 0),            # ratio_SExt_insts
                ratios.get("ratio SIToFP insts", 0),          # ratio_SIToFP_insts
                ratios.get("ratio SRem insts", 0),            # ratio_SRem_insts
                ratios.get("ratio Select insts", 0),          # ratio_Select_insts
                ratios.get("ratio Shl insts", 0),             # ratio_Shl_insts
                ratios.get("ratio Store insts", 0),           # ratio_Store_insts
                ratios.get("ratio Sub insts", 0),             # ratio_Sub_insts
                ratios.get("ratio Trunc insts", 0),           # ratio_Trunc_insts
                ratios.get("ratio UDiv insts", 0),            # ratio_UDiv_insts
                ratios.get("ratio Xor insts", 0),             # ratio_Xor_insts
                ratios.get("ratio ZExt insts", 0),            # ratio_ZExt_insts
                ratios.get("ratio basic blocks", 0),          # ratio_basic_blocks
                ratios.get("ratio memory instructions", 0),   # ratio_memory_instructions
                ratios.get("ratio non-external functions", 0) # ratio_non_external_functions
            )

            placeholders = ",".join(["?"] * len(features))
            self.execute("INSERT INTO kernel_features VALUES ({placeholders})"
                         .format(placeholders=placeholders), features)
        self.commit()

    def populate_device_features_table(self):
        """
        Derive device features from "devices" table.
        """
        self.execute("INSERT INTO device_features SELECT * FROM devices")
        self.commit()

    def populate_dataset_features_table(self):
        """
        Derive dataset features from "datasets" table.
        """
        self.execute("INSERT INTO dataset_features SELECT * FROM datasets")
        self.commit()

    def populate_runtime_stats_table(self):
        """
        Derive runtime stats from "runtimes" table.
        """
        query = self.execute("SELECT scenario,params FROM runtimes "
                             "GROUP BY scenario,params")
        rows = query.fetchall()
        total = len(rows)
        i = 0
        for row in rows:
            scenario, params = row
            i += 1

            # Gather statistics about runtimes for each scenario,params pair.
            self.execute("INSERT INTO runtime_stats SELECT scenario,params,"
                         "COUNT(runtime),MIN(runtime),AVG(runtime),MAX(runtime) "
                         "FROM runtimes WHERE scenario=? AND params=?",
                         (scenario, params))

            # Intermediate progress reports.
            if not i % 10:
                # Commit progress.
                self.commit()
                io.info("Creating runtime_stats ... {0:02.3f}%."
                        .format((i / total) * 100))
        self.commit()

    def populate_oracle_params_table(self):
        """
        Derive oracle params from "runtime_stats" table.
        """
        query = self.execute("SELECT distinct scenario FROM runtime_stats")
        rows = query.fetchall()
        total = len(rows)
        i = 0
        for row in rows:
            scenario = row[0]
            i += 1

            # Lookup best params for each scenario.
            self.execute("INSERT INTO oracle_params SELECT "
                         "scenario,params,num_samples,mean as mean_runtime "
                         "FROM runtime_stats WHERE scenario=? and "
                         "mean=(select min(mean) FROM runtime_stats "
                         "WHERE scenario=?)", (scenario, scenario))

            # Intermediate progress reports.
            if not i % 10:
                # Commit progress.
                self.commit()
                io.info("Creating oracle_params ... {0:02.3f}%."
                        .format((i / total) * 100))
        self.commit()

    def populate_features_runtime_stats_table(self):
        self.execute(POPULATE_FEATURES_RUNTIME_STATS_TABLE)
        self.commit()

    def populate_features_oracle_params_table(self):
        self.execute(POPULATE_FEATURES_ORACLE_PARAMS_TABLE)
        self.commit()

    def populate_tables(self):
        """
        Populate the derived tables from the base database.
        """
        self.populate_kernel_features_table()
        self.populate_device_features_table()
        self.populate_dataset_features_table()
        self.populate_runtime_stats_table()
        self.populate_oracle_params_table()
        self.populate_features_runtime_stats_table()
        self.populate_features_oracle_params_table()
        self.execute("VACUUM")

    def export_oracle_arff(self, output=None):
        types = (
            "NUMERIC", # data_width
            "NUMERIC", # data_height
            "NOMINAL", # data_tin
            "NOMINAL", # data_tout
            "NUMERIC", # kern_north
            "NUMERIC", # kern_south
            "NUMERIC", # kern_east
            "NUMERIC", # kern_west
            "NUMERIC", # kern_max_wg_size
            "NUMERIC", # kern_instruction_count
            "NUMERIC", # kern_ratio_AShr_insts
            "NUMERIC", # kern_ratio_Add_insts
            "NUMERIC", # kern_ratio_Alloca_insts
            "NUMERIC", # kern_ratio_And_insts
            "NUMERIC", # kern_ratio_Br_insts
            "NUMERIC", # kern_ratio_Call_insts
            "NUMERIC", # kern_ratio_FAdd_insts
            "NUMERIC", # kern_ratio_FCmp_insts
            "NUMERIC", # kern_ratio_FDiv_insts
            "NUMERIC", # kern_ratio_FMul_insts
            "NUMERIC", # kern_ratio_FPExt_insts
            "NUMERIC", # kern_ratio_FPToSI_insts
            "NUMERIC", # kern_ratio_FSub_insts
            "NUMERIC", # kern_ratio_GetElementPtr_insts
            "NUMERIC", # kern_ratio_ICmp_insts
            "NUMERIC", # kern_ratio_InsertValue_insts
            "NUMERIC", # kern_ratio_Load_insts
            "NUMERIC", # kern_ratio_Mul_insts
            "NUMERIC", # kern_ratio_Or_insts
            "NUMERIC", # kern_ratio_PHI_insts
            "NUMERIC", # kern_ratio_Ret_insts
            "NUMERIC", # kern_ratio_SDiv_insts
            "NUMERIC", # kern_ratio_SExt_insts
            "NUMERIC", # kern_ratio_SIToFP_insts
            "NUMERIC", # kern_ratio_SRem_insts
            "NUMERIC", # kern_ratio_Select_insts
            "NUMERIC", # kern_ratio_Shl_insts
            "NUMERIC", # kern_ratio_Store_insts
            "NUMERIC", # kern_ratio_Sub_insts
            "NUMERIC", # kern_ratio_Trunc_insts
            "NUMERIC", # kern_ratio_UDiv_insts
            "NUMERIC", # kern_ratio_Xor_insts
            "NUMERIC", # kern_ratio_ZExt_insts
            "NUMERIC", # kern_ratio_basic_blocks
            "NUMERIC", # kern_ratio_memory_instructions
            "NUMERIC", # kern_ratio_non_external_functions
            "NUMERIC", # dev_count
            "NUMERIC", # dev_address_bits
            "NUMERIC", # dev_double_fp_config
            "NUMERIC", # dev_endian_little
            "NUMERIC", # dev_execution_capabilities
            "NOMINAL", # dev_extensions
            "NUMERIC", # dev_global_mem_cache_size
            "NUMERIC", # dev_global_mem_cache_type
            "NUMERIC", # dev_global_mem_cacheline_size
            "NUMERIC", # dev_global_mem_size
            "NUMERIC", # dev_host_unified_memory
            "NUMERIC", # dev_image2d_max_height
            "NUMERIC", # dev_image2d_max_width
            "NUMERIC", # dev_image3d_max_depth
            "NUMERIC", # dev_image3d_max_height
            "NUMERIC", # dev_image3d_max_width
            "NUMERIC", # dev_image_support
            "NUMERIC", # dev_local_mem_size
            "NUMERIC", # dev_local_mem_type
            "NUMERIC", # dev_max_clock_frequency
            "NUMERIC", # dev_max_compute_units
            "NUMERIC", # dev_max_constant_args
            "NUMERIC", # dev_max_constant_buffer_size
            "NUMERIC", # dev_max_mem_alloc_size
            "NUMERIC", # dev_max_parameter_size
            "NUMERIC", # dev_max_read_image_args
            "NUMERIC", # dev_max_samplers
            "NUMERIC", # dev_max_work_group_size
            "NUMERIC", # dev_max_work_item_dimensions
            "NUMERIC", # dev_max_work_item_sizes_0
            "NUMERIC", # dev_max_work_item_sizes_1
            "NUMERIC", # dev_max_work_item_sizes_2
            "NUMERIC", # dev_max_write_image_args
            "NUMERIC", # dev_mem_base_addr_align
            "NUMERIC", # dev_min_data_type_align_size
            "NUMERIC", # dev_native_vector_width_char
            "NUMERIC", # dev_native_vector_width_double
            "NUMERIC", # dev_native_vector_width_float
            "NUMERIC", # dev_native_vector_width_half
            "NUMERIC", # dev_native_vector_width_int
            "NUMERIC", # dev_native_vector_width_long
            "NUMERIC", # dev_native_vector_width_short
            "NUMERIC", # dev_preferred_vector_width_char
            "NUMERIC", # dev_preferred_vector_width_double
            "NUMERIC", # dev_preferred_vector_width_float
            "NUMERIC", # dev_preferred_vector_width_half
            "NUMERIC", # dev_preferred_vector_width_int
            "NUMERIC", # dev_preferred_vector_width_long
            "NUMERIC", # dev_preferred_vector_width_short
            "NUMERIC", # dev_queue_properties
            "NUMERIC", # dev_single_fp_config
            "NUMERIC", # dev_type
            "NOMINAL", # dev_vendor
            "NOMINAL", # dev_vendor_id
            "NOMINAL", # dev_version
            "NOMINAL"  # wgsize
        )
        self.export_arff("features_oracle_params",
                         output=output, types=types)

    @staticmethod
    def init_from_db(dst, src):
        """
        Create and populate the tables of
        """
        fs.cp(src.path, dst)
        db = MLDatabase(dst)
        db.create_tables()
        db.populate_tables()

        db.commit()
        return db


def create_test_db(dst, src, num_runtimes=100000):
    """
    Create a reduced-size database for testing.

    A copy of the source database is made, but "num_runtimes" are
    selected randomly. This is to allow faster testing on smaller
    databases.

    Arguments:

        dst (path): The path to the destination database.
        src (Database): The source database.
        num_runtimes (int, optional): The maximum number of runtimes
          to keep.

    Returns:

        Database: The reduced test database.
    """
    io.info("Creating test database of {n} runtimes"
            .format(n=num_runtimes))

    fs.cp(src.path, dst)
    test = Database(dst)

    # Copy old runtimes table.
    test.copy_table("runtimes", "runtimes_tmp")
    test.drop_table("runtimes")

    # Create new runtimes table.
    test.create_table_from("runtimes", "runtimes_tmp")
    cmd = ("INSERT INTO runtimes SELECT * FROM runtimes_tmp "
           "ORDER BY RANDOM() LIMIT {n}".format(n=num_runtimes))
    test.execute(cmd)
    test.drop_table("runtimes_tmp")

    # Remove unused scenarios.
    test.execute("DELETE FROM scenarios WHERE id NOT IN "
                 "(SELECT DISTINCT scenario from runtimes)")

    # Remove unused kernels.
    test.execute("DELETE FROM kernels WHERE id NOT IN "
                 "(SELECT DISTINCT kernel from scenarios)")
    # Remove unused devices.
    test.execute("DELETE FROM devices WHERE id NOT IN "
                 "(SELECT DISTINCT device from scenarios)")
    # Remove unused datasets.
    test.execute("DELETE FROM datasets WHERE id NOT IN "
                 "(SELECT DISTINCT dataset from scenarios)")

    test.commit()

    # Shrink database to reclaim lost space.
    test.execute("VACUUM")

    return test
