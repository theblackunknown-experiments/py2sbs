// Created by ThiSpawn - 2013
// License Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License.

// https://www.shadertoy.com/view/lss3DS

// the base unit is the meter !

//===============================================================================================
// MATH CONSTANTS
//===============================================================================================

const float PI = 3.14159265358979323846;
const float PI_2 = 1.57079632679489661923;
const float PI_4 = 0.785398163397448309616;

//===============================================================================================
// COLOR SPACE TOOLS
//===============================================================================================

const mat3 mRGB2XYZ = mat3(0.5141364, 0.3238786 , 0.16036376,
                           0.265068 , 0.67023428, 0.06409157,
                           0.0241188, 0.1228178 , 0.84442666);

const mat3 mXYZ2RGB = mat3( 2.5651, -1.1665, -0.3986,
                           -1.0217,  1.9777,  0.0439,
                            0.0753, -0.2543,  1.1892);

vec3 rgb_to_yxy(vec3 cRGB)
{
    vec3 cYxy;
    vec3 cXYZ = mRGB2XYZ * cRGB;
    cYxy.r = cXYZ.g;
    float temp = dot(vec3(1.0, 1.0, 1.0), cXYZ.rgb);
    cYxy.gb = cXYZ.rg / temp;
    return cYxy;
}

vec3 yxy_to_rgb(vec3 cYxy)
{
    vec3 cXYZ = vec3(cYxy.r * cYxy.g / cYxy.b,
                     cYxy.r,
                     cYxy.r * (1.0 - cYxy.g - cYxy.b) / cYxy.b);
    return mXYZ2RGB * cXYZ;
}

const vec3 vGammaPowerInverse = vec3(2.2);
const vec3 vGammaPower = vec3(0.454545);

vec3 linear_to_gamma(vec3 c)
{
    return pow(clamp(c, 0.0, 1.0), vGammaPower);
}

vec3 gamma_to_linear(vec3 c)
{
    return pow(clamp(c, 0.0, 1.0), vGammaPowerInverse);
}

//===============================================================================================
// SCENE PARAMETERS
//===============================================================================================

// North is pointed by x
// East is pointed by z
// Sea Level : y = 0.0

struct slight // spotlight
{
    vec3 pos;   // position
    vec3 d;     // diameter
    float i;    // intensity
    vec3 c;     // color
};

// TODO : fix misplaced stuff from sun_t to planet_t

struct planet_t
{
    float rs;       // sea level radius
    float ra;       // atmosphere radius
    vec3  beta_r;   // rayleigh scattering coefs at sea level
    vec3  beta_m;   // mie scattering coefs at sea level
    float sh_r;     // rayleigh scale height
    float sh_m;     // mie scale height
};

planet_t earth = planet_t(
    6360.0e3, 6420.0e3,
    vec3(5.5e-6, 13.0e-6, 22.1e-6),
    vec3(18.0e-6), // looks better than 21
    7994.0, 1200.0
);

struct sun_t
{
    float i;        // sun intensity
    float mc;       // mean cosine
    float azi;      // azimuth
    float alt;      // altitude
    float ad;       // angular diameter (between 0.5244 and 0.5422 for our sun)
    vec3 color;
};

sun_t sun = sun_t(
    20.0,
    0.76,
    4.4,
    PI_2,
    0.009250245, // 0.53 degree
    vec3(1.0, 1.0, 1.0)
);

// Use http://www.esrl.noaa.gov/gmd/grad/solcalc/azel.html to get azimuth and altitude
// of our sun at a specific place and time

//===============================================================================================
// RAY MARCHING STUFF
//===============================================================================================

// pred : rd is normalized
bool intersect_with_atmosphere(in vec3 ro, in vec3 rd, in planet_t planet, out float tr)
{
    float c = length(ro); // distance from center of the planet :)
    vec3 up_dir = ro / c;
    float beta = PI - acos(dot(rd, up_dir));
    float sb = sin(beta);
    float b = planet.ra;
    float bt = planet.rs - 10.0;

    tr = sqrt((b * b) - (c * c) * (sb * sb)) + c * cos(beta); // sinus law

    if (sqrt((bt * bt) - (c * c) * (sb * sb)) + c * cos(beta) > 0.0)
        return false;

    return true;
}

const int SKYLIGHT_NB_VIEWDIR_SAMPLES = 12;
const int SKYLIGHT_NB_SUNDIR_SAMPLES = 6;

float compute_sun_visibility(in sun_t sun, float alt)
{
    float vap = 0.0;
    float h, a;
    float vvp = clamp((0.5 + alt / sun.ad), 0.0, 1.0); // vertically visible percentage
    if (vvp == 0.0)
        return 0.0;
    else if (vvp == 1.0)
        return 1.0;

    bool is_sup;

    if (vvp > 0.5)
    {
        is_sup = true;
        h = (vvp - 0.5) * 2.0;
    }
    else
    {
        is_sup = false;
        h = (0.5 - vvp) * 2.0;
    }

    float alpha = acos(h) * 2.0;
    a = (alpha - sin(alpha)) / (2.0 * PI);

    if (is_sup)
        vap = 1.0 - a;
    else
        vap = a;

    return vap;
}

// pred : rd is normalized
vec3 compute_sky_light(in vec3 ro, in vec3 rd, in planet_t planet, in sun_t sun)
{
    float t1;

    if (!intersect_with_atmosphere(ro, rd, planet, t1) || t1 < 0.0)
        return vec3(0.0);

    float sl = t1 / float(SKYLIGHT_NB_VIEWDIR_SAMPLES); // seg length
    float t = 0.0;

    float calt = cos(sun.alt);
    vec3 sun_dir = vec3(cos(sun.azi) * calt,
                        sin(sun.alt),
                        sin(sun.azi) * calt);
    float mu = dot(rd, sun_dir);

    float mu2 = mu * mu;
    float mc2 = sun.mc * sun.mc;

    // rayleigh stuff
    vec3 sumr = vec3(0.0);
    float odr = 0.0; // optical depth
    float phase_r = (3.0 / (16.0 * PI)) * (1.0 + mu2);

    // mie stuff
    vec3 summ = vec3(0.0);
    float odm = 0.0; // optical depth
    float phase_m = ((3.0 / (8.0 * PI)) * ((1.0 - mc2) * (1.0 + mu2))) /
                    ((2.0 + mc2) * pow(1.0 + mc2 - 2.0 * sun.mc * mu, 1.5));

    for (int i = 0; i < SKYLIGHT_NB_VIEWDIR_SAMPLES; ++i)
    {
        vec3 sp = ro + rd * (t + 0.5 * sl);
        float h = length(sp) - planet.rs;
        float hr = exp(-h / planet.sh_r) * sl;
        odr += hr;
        float hm = exp(-h / planet.sh_m) * sl;
        odm += hm;
        float tm;
        float sp_alt = PI_2 - asin(planet.rs / length(sp));
        sp_alt += acos(normalize(sp).y) + sun.alt;
        float coef = compute_sun_visibility(sun, sp_alt);
        if (intersect_with_atmosphere(sp, sun_dir, planet, tm) || coef > 0.0)
        {
            float sll = tm / float(SKYLIGHT_NB_SUNDIR_SAMPLES);
            float odlr = 0.0;
            float odlm = 0.0;
            for (int j = 0; j < SKYLIGHT_NB_SUNDIR_SAMPLES; ++j)
            {
                vec3 spl = sp + sun_dir * ((float(j) + 0.5) * sll);
                float spl_alt = PI_2 - asin(planet.rs / length(spl));
                spl_alt += acos(normalize(spl).y) + sun.alt;
                float coefl = compute_sun_visibility(sun, spl_alt);
                float hl = length(spl) - planet.rs;
                odlr += exp(-hl / planet.sh_r) * sll * (1.0 - log(coefl + 0.000001));
                odlm += exp(-hl / planet.sh_m) * sll * (1.0 - log(coefl + 0.000001));

            }
            vec3 tau_m = planet.beta_m * 1.05 * (odm + odlm);
            vec3 tau_r = planet.beta_r * (odr + odlr);
            vec3 tau = tau_m + tau_r;
            vec3 attenuation = exp(-tau);
            sumr += hr * attenuation * coef;
            summ += hm * attenuation * coef;
        }
        t += sl;
    }
    float direct_coef = 1.0;
    if (acos(mu) < sun.ad * 0.6) // makes it a bit bigger
        direct_coef = 3.0 + sin(mu / (sun.ad * 0.5)) * 3.0;
    return 0.8 * sun.i * direct_coef * (sumr * phase_r * planet.beta_r + summ * phase_m * planet.beta_m);
}

//===============================================================================================
// MAIN
//===============================================================================================

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    vec2 q = fragCoord.xy / iResolution.xy;
    vec2 p = -1.0 + 2.0*q;
    p.x *= iResolution.x / iResolution.y;
    float view_coef = 0.8;
    if (p.y < 0.0)
    {
        p.y = 1.0 + p.y;
        view_coef = 4.8;
    }

    vec3 c_position = vec3(0.0, 1.0, 0.0);
    vec3 c_lookat   = vec3(-0.04, 1.0, -1.0);
    vec3 c_updir    = vec3(0.0, 1.0, 0.0);

    vec3 view_dir = normalize(c_lookat - c_position);

    vec3 uu = normalize(cross(view_dir, c_updir));
    vec3 vv = normalize(cross(uu, view_dir));
    vec3 rd = normalize(p.x * uu + p.y * vv + view_coef * view_dir);

    sun.alt = 4.0 * -sun.ad + 1.6 * PI_4 * (0.5 + cos(0.46 * iTime) / 2.0);

    vec3 gp = c_position + vec3(0.0, earth.rs + 1.0, 0.0);
    vec3 res = compute_sky_light(gp, rd, earth, sun);

    //================================
    // POST EFFECTS

    if(q.x > 0.0 )
    {
        float crush = 0.6;
        float frange = 7.9;
        float exposure = 48.0;
        res = log2(1.0+res*exposure);
        res = smoothstep(crush, frange, res);
        res = res*res*res*(res*(res*6.0 - 15.0) + 10.0);
    }

    if (q.y < 0.5 && q.y > 0.498)
        res = vec3(0.0);

    // switch to gamma space before perceptual tweaks
    res = linear_to_gamma(res);

    // vignetting
    // tensor product of the parametric curve defined by (4(t-tÂ²))^0.1
    res *= 0.5 + 0.5 * pow(16.0 * q.x * q.y * (1.0 - q.x) * (1.0 - q.y), 0.1);


    fragColor = vec4(res, 1.0);
}
