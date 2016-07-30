typedef enum {
  C = 0,
  N,
  S,
  E,
  W,
  T,
  B,
  NE,
  NW,
  SE,
  SW,
  NT,
  NB,
  ST,
  SB,
  ET,
  EB,
  WT,
  WB,
  FLAGS,
  N_CELL_ENTRIES
} CELL_ENTRIES;

typedef enum {
  OBSTACLE = 1 << 0,
  ACCEL = 1 << 1,
  IN_OUT_FLOW = 1 << 2
} CELL_FLAGS;
typedef float* LBM_Grid;
typedef LBM_Grid* LBM_GridPtr;
__kernel void A(__global float* a, __global float* b) {
  a +=
      ((0 +
        N_CELL_ENTRIES *
            ((0) + (0) * ((120) + (8)) + (2) * ((120) + (8)) * ((120) + (0)))) -
       (0 +
        N_CELL_ENTRIES *
            ((0) + (0) * ((120) + (8)) + (0) * ((120) + (8)) * ((120) + (0)))));
  b +=
      ((0 +
        N_CELL_ENTRIES *
            ((0) + (0) * ((120) + (8)) + (2) * ((120) + (8)) * ((120) + (0)))) -
       (0 +
        N_CELL_ENTRIES *
            ((0) + (0) * ((120) + (8)) + (0) * ((120) + (8)) * ((120) + (0)))));

  int c, d, e;
  c = get_local_id(0);
  d = get_group_id(0);
  e = get_group_id(1);

  float f, g, h, i, j, k, l, m;
  float n, o, p, q, r, s, t;
  float u, v, w, x, y;

  g = ((((a)[(C +
              N_CELL_ENTRIES * (((0) + c) + ((0) + d) * ((120) + (8)) +
                                ((0) + e) * ((120) + (8)) * ((120) + (0))))])));

  h = ((((a)[(N +
              N_CELL_ENTRIES * (((0) + c) + ((-1) + d) * ((120) + (8)) +
                                ((0) + e) * ((120) + (8)) * ((120) + (0))))])));
  i = ((((a)[(S +
              N_CELL_ENTRIES * (((0) + c) + ((+1) + d) * ((120) + (8)) +
                                ((0) + e) * ((120) + (8)) * ((120) + (0))))])));
  j = ((((a)[(E +
              N_CELL_ENTRIES * (((-1) + c) + ((0) + d) * ((120) + (8)) +
                                ((0) + e) * ((120) + (8)) * ((120) + (0))))])));
  k = ((((a)[(W +
              N_CELL_ENTRIES * (((+1) + c) + ((0) + d) * ((120) + (8)) +
                                ((0) + e) * ((120) + (8)) * ((120) + (0))))])));
  l = ((
      ((a)[(T +
            N_CELL_ENTRIES * (((0) + c) + ((0) + d) * ((120) + (8)) +
                              ((-1) + e) * ((120) + (8)) * ((120) + (0))))])));
  m = ((
      ((a)[(B +
            N_CELL_ENTRIES * (((0) + c) + ((0) + d) * ((120) + (8)) +
                              ((+1) + e) * ((120) + (8)) * ((120) + (0))))])));

  n = ((((a)[(NE +
              N_CELL_ENTRIES * (((-1) + c) + ((-1) + d) * ((120) + (8)) +
                                ((0) + e) * ((120) + (8)) * ((120) + (0))))])));
  o = ((((a)[(NW +
              N_CELL_ENTRIES * (((+1) + c) + ((-1) + d) * ((120) + (8)) +
                                ((0) + e) * ((120) + (8)) * ((120) + (0))))])));
  p = ((((a)[(SE +
              N_CELL_ENTRIES * (((-1) + c) + ((+1) + d) * ((120) + (8)) +
                                ((0) + e) * ((120) + (8)) * ((120) + (0))))])));
  q = ((((a)[(SW +
              N_CELL_ENTRIES * (((+1) + c) + ((+1) + d) * ((120) + (8)) +
                                ((0) + e) * ((120) + (8)) * ((120) + (0))))])));
  r = ((
      ((a)[(NT +
            N_CELL_ENTRIES * (((0) + c) + ((-1) + d) * ((120) + (8)) +
                              ((-1) + e) * ((120) + (8)) * ((120) + (0))))])));
  s = ((
      ((a)[(NB +
            N_CELL_ENTRIES * (((0) + c) + ((-1) + d) * ((120) + (8)) +
                              ((+1) + e) * ((120) + (8)) * ((120) + (0))))])));
  t = ((
      ((a)[(ST +
            N_CELL_ENTRIES * (((0) + c) + ((+1) + d) * ((120) + (8)) +
                              ((-1) + e) * ((120) + (8)) * ((120) + (0))))])));
  u = ((
      ((a)[(SB +
            N_CELL_ENTRIES * (((0) + c) + ((+1) + d) * ((120) + (8)) +
                              ((+1) + e) * ((120) + (8)) * ((120) + (0))))])));
  v = ((
      ((a)[(ET +
            N_CELL_ENTRIES * (((-1) + c) + ((0) + d) * ((120) + (8)) +
                              ((-1) + e) * ((120) + (8)) * ((120) + (0))))])));
  w = ((
      ((a)[(EB +
            N_CELL_ENTRIES * (((-1) + c) + ((0) + d) * ((120) + (8)) +
                              ((+1) + e) * ((120) + (8)) * ((120) + (0))))])));
  x = ((
      ((a)[(WT +
            N_CELL_ENTRIES * (((+1) + c) + ((0) + d) * ((120) + (8)) +
                              ((-1) + e) * ((120) + (8)) * ((120) + (0))))])));
  y = ((
      ((a)[(WB +
            N_CELL_ENTRIES * (((+1) + c) + ((0) + d) * ((120) + (8)) +
                              ((+1) + e) * ((120) + (8)) * ((120) + (0))))])));

  if (__builtin_astype(
          (((a)[(FLAGS +
                 N_CELL_ENTRIES *
                     (((0) + c) + ((0) + d) * ((120) + (8)) +
                      ((0) + e) * ((120) + (8)) * ((120) + (0))))])),
          uint) &
      (OBSTACLE)) {
    f = h;
    h = i;
    i = f;
    f = j;
    j = k;
    k = f;
    f = l;
    l = m;
    m = f;
    f = n;
    n = q;
    q = f;
    f = o;
    o = p;
    p = f;
    f = r;
    r = u;
    u = f;
    f = s;
    s = t;
    t = f;
    f = v;
    v = y;
    y = f;
    f = w;
    w = x;
    x = f;
  } else {
    float z, aa, ab, ac, ad;
    float ae, af, ag;
    ac = g + h + i + j + k + l + m + n + o + p + q + r + s + t + u + v + w + x +
         y;

    z = +j - k + n - o + p - q + v + w - x - y;

    aa = +h - i + n + o - p - q + r + s - t - u;

    ab = +l - m + r - s + t - u + v - w + x - y;

    z /= ac;
    aa /= ac;
    ab /= ac;

    if (__builtin_astype(
            (((a)[(FLAGS +
                   N_CELL_ENTRIES *
                       (((0) + c) + ((0) + d) * ((120) + (8)) +
                        ((0) + e) * ((120) + (8)) * ((120) + (0))))])),
            uint) &
        (ACCEL)) {
      z = 0.005f;
      aa = 0.002f;
      ab = 0.000f;
    }

    ad = 1.5f * (z * z + aa * aa + ab * ab) - 1.0f;
    ag = (1.95f) * ac;
    ae = (1.0f / 3.0f) * ag;

    ag = (1.95f) * ac;
    ae = (1.0f / 3.0f) * ag;
    af = 1.0f - (1.95f);
    g = af * g + ae * (-ad);
    ae = (1.0f / 18.0f) * ag;
    h = af * h + ae * (aa * (4.5f * aa + 3.0f) - ad);
    i = af * i + ae * (aa * (4.5f * aa - 3.0f) - ad);
    l = af * l + ae * (ab * (4.5f * ab + 3.0f) - ad);
    m = af * m + ae * (ab * (4.5f * ab - 3.0f) - ad);
    j = af * j + ae * (z * (4.5f * z + 3.0f) - ad);
    k = af * k + ae * (z * (4.5f * z - 3.0f) - ad);
    ae = (1.0f / 36.0f) * ag;
    r = af * r + ae * ((+aa + ab) * (4.5f * (+aa + ab) + 3.0f) - ad);
    s = af * s + ae * ((+aa - ab) * (4.5f * (+aa - ab) + 3.0f) - ad);
    t = af * t + ae * ((-aa + ab) * (4.5f * (-aa + ab) + 3.0f) - ad);
    u = af * u + ae * ((-aa - ab) * (4.5f * (-aa - ab) + 3.0f) - ad);
    n = af * n + ae * ((+z + aa) * (4.5f * (+z + aa) + 3.0f) - ad);
    p = af * p + ae * ((+z - aa) * (4.5f * (+z - aa) + 3.0f) - ad);
    v = af * v + ae * ((+z + ab) * (4.5f * (+z + ab) + 3.0f) - ad);
    w = af * w + ae * ((+z - ab) * (4.5f * (+z - ab) + 3.0f) - ad);
    o = af * o + ae * ((-z + aa) * (4.5f * (-z + aa) + 3.0f) - ad);
    q = af * q + ae * ((-z - aa) * (4.5f * (-z - aa) + 3.0f) - ad);
    x = af * x + ae * ((-z + ab) * (4.5f * (-z + ab) + 3.0f) - ad);
    y = af * y + ae * ((-z - ab) * (4.5f * (-z - ab) + 3.0f) - ad);
  }

  ((((b)[(C +
          N_CELL_ENTRIES * (((0) + c) + ((0) + d) * ((120) + (8)) +
                            ((0) + e) * ((120) + (8)) * ((120) + (0))))]))) = g;

  ((((b)[(N +
          N_CELL_ENTRIES * (((0) + c) + ((0) + d) * ((120) + (8)) +
                            ((0) + e) * ((120) + (8)) * ((120) + (0))))]))) = h;
  ((((b)[(S +
          N_CELL_ENTRIES * (((0) + c) + ((0) + d) * ((120) + (8)) +
                            ((0) + e) * ((120) + (8)) * ((120) + (0))))]))) = i;
  ((((b)[(E +
          N_CELL_ENTRIES * (((0) + c) + ((0) + d) * ((120) + (8)) +
                            ((0) + e) * ((120) + (8)) * ((120) + (0))))]))) = j;
  ((((b)[(W +
          N_CELL_ENTRIES * (((0) + c) + ((0) + d) * ((120) + (8)) +
                            ((0) + e) * ((120) + (8)) * ((120) + (0))))]))) = k;
  ((((b)[(T +
          N_CELL_ENTRIES * (((0) + c) + ((0) + d) * ((120) + (8)) +
                            ((0) + e) * ((120) + (8)) * ((120) + (0))))]))) = l;
  ((((b)[(B +
          N_CELL_ENTRIES * (((0) + c) + ((0) + d) * ((120) + (8)) +
                            ((0) + e) * ((120) + (8)) * ((120) + (0))))]))) = m;

  ((((b)[(NE +
          N_CELL_ENTRIES * (((0) + c) + ((0) + d) * ((120) + (8)) +
                            ((0) + e) * ((120) + (8)) * ((120) + (0))))]))) = n;
  ((((b)[(NW +
          N_CELL_ENTRIES * (((0) + c) + ((0) + d) * ((120) + (8)) +
                            ((0) + e) * ((120) + (8)) * ((120) + (0))))]))) = o;
  ((((b)[(SE +
          N_CELL_ENTRIES * (((0) + c) + ((0) + d) * ((120) + (8)) +
                            ((0) + e) * ((120) + (8)) * ((120) + (0))))]))) = p;
  ((((b)[(SW +
          N_CELL_ENTRIES * (((0) + c) + ((0) + d) * ((120) + (8)) +
                            ((0) + e) * ((120) + (8)) * ((120) + (0))))]))) = q;
  ((((b)[(NT +
          N_CELL_ENTRIES * (((0) + c) + ((0) + d) * ((120) + (8)) +
                            ((0) + e) * ((120) + (8)) * ((120) + (0))))]))) = r;
  ((((b)[(NB +
          N_CELL_ENTRIES * (((0) + c) + ((0) + d) * ((120) + (8)) +
                            ((0) + e) * ((120) + (8)) * ((120) + (0))))]))) = s;
  ((((b)[(ST +
          N_CELL_ENTRIES * (((0) + c) + ((0) + d) * ((120) + (8)) +
                            ((0) + e) * ((120) + (8)) * ((120) + (0))))]))) = t;
  ((((b)[(SB +
          N_CELL_ENTRIES * (((0) + c) + ((0) + d) * ((120) + (8)) +
                            ((0) + e) * ((120) + (8)) * ((120) + (0))))]))) = u;
  ((((b)[(ET +
          N_CELL_ENTRIES * (((0) + c) + ((0) + d) * ((120) + (8)) +
                            ((0) + e) * ((120) + (8)) * ((120) + (0))))]))) = v;
  ((((b)[(EB +
          N_CELL_ENTRIES * (((0) + c) + ((0) + d) * ((120) + (8)) +
                            ((0) + e) * ((120) + (8)) * ((120) + (0))))]))) = w;
  ((((b)[(WT +
          N_CELL_ENTRIES * (((0) + c) + ((0) + d) * ((120) + (8)) +
                            ((0) + e) * ((120) + (8)) * ((120) + (0))))]))) = x;
  ((((b)[(WB +
          N_CELL_ENTRIES * (((0) + c) + ((0) + d) * ((120) + (8)) +
                            ((0) + e) * ((120) + (8)) * ((120) + (0))))]))) = y;
}