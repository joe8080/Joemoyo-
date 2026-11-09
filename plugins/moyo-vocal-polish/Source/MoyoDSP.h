#pragma once

#include <cmath>
#include <algorithm>

// Small, allocation-free DSP building blocks used by MOYO Vocal Polish.
namespace moyo
{
constexpr double kPi = 3.14159265358979323846;

inline float dbToGain (float db) noexcept { return std::pow (10.0f, db * 0.05f); }
inline float gainToDb (float g) noexcept  { return 20.0f * std::log10 (std::max (g, 1.0e-9f)); }

// RBJ "Audio EQ Cookbook" biquad, transposed direct form II.
struct Biquad
{
    float b0 = 1, b1 = 0, b2 = 0, a1 = 0, a2 = 0;
    float z1 = 0, z2 = 0;

    void reset() noexcept { z1 = z2 = 0; }

    inline float process (float x) noexcept
    {
        const float y = b0 * x + z1;
        z1 = b1 * x - a1 * y + z2;
        z2 = b2 * x - a2 * y;
        return y;
    }

    void set (double nb0, double nb1, double nb2, double na0, double na1, double na2) noexcept
    {
        b0 = (float) (nb0 / na0); b1 = (float) (nb1 / na0); b2 = (float) (nb2 / na0);
        a1 = (float) (na1 / na0); a2 = (float) (na2 / na0);
    }

    void highPass (double fs, double f, double q) noexcept
    {
        const double w = 2.0 * kPi * f / fs, c = std::cos (w), al = std::sin (w) / (2.0 * q);
        set ((1 + c) / 2, -(1 + c), (1 + c) / 2, 1 + al, -2 * c, 1 - al);
    }

    void lowPass (double fs, double f, double q) noexcept
    {
        const double w = 2.0 * kPi * f / fs, c = std::cos (w), al = std::sin (w) / (2.0 * q);
        set ((1 - c) / 2, 1 - c, (1 - c) / 2, 1 + al, -2 * c, 1 - al);
    }

    void bandPass (double fs, double f, double q) noexcept
    {
        const double w = 2.0 * kPi * f / fs, c = std::cos (w), al = std::sin (w) / (2.0 * q);
        set (al, 0, -al, 1 + al, -2 * c, 1 - al);
    }

    void peak (double fs, double f, double q, double gainDb) noexcept
    {
        const double A = std::pow (10.0, gainDb / 40.0);
        const double w = 2.0 * kPi * f / fs, c = std::cos (w), al = std::sin (w) / (2.0 * q);
        set (1 + al * A, -2 * c, 1 - al * A, 1 + al / A, -2 * c, 1 - al / A);
    }

    void lowShelf (double fs, double f, double gainDb) noexcept
    {
        const double A = std::pow (10.0, gainDb / 40.0);
        const double w = 2.0 * kPi * f / fs, c = std::cos (w), s = std::sin (w);
        const double al = s / 2.0 * std::sqrt (2.0); // shelf slope S = 1
        const double t = 2.0 * std::sqrt (A) * al;
        set (A * ((A + 1) - (A - 1) * c + t),
             2 * A * ((A - 1) - (A + 1) * c),
             A * ((A + 1) - (A - 1) * c - t),
             (A + 1) + (A - 1) * c + t,
             -2 * ((A - 1) + (A + 1) * c),
             (A + 1) + (A - 1) * c - t);
    }

    void highShelf (double fs, double f, double gainDb) noexcept
    {
        const double A = std::pow (10.0, gainDb / 40.0);
        const double w = 2.0 * kPi * f / fs, c = std::cos (w), s = std::sin (w);
        const double al = s / 2.0 * std::sqrt (2.0);
        const double t = 2.0 * std::sqrt (A) * al;
        set (A * ((A + 1) + (A - 1) * c + t),
             -2 * A * ((A - 1) + (A + 1) * c),
             A * ((A + 1) + (A - 1) * c - t),
             (A + 1) - (A - 1) * c + t,
             2 * ((A - 1) - (A + 1) * c),
             (A + 1) - (A - 1) * c - t);
    }
};

// Attack/release envelope follower working in the linear domain.
struct Envelope
{
    float attackCoef = 0, releaseCoef = 0, value = 0;

    void setTimes (double fs, double attackMs, double releaseMs) noexcept
    {
        attackCoef  = (float) std::exp (-1.0 / (0.001 * attackMs  * fs));
        releaseCoef = (float) std::exp (-1.0 / (0.001 * releaseMs * fs));
    }

    void reset() noexcept { value = 0; }

    inline float process (float in) noexcept
    {
        const float coef = in > value ? attackCoef : releaseCoef;
        value = in + coef * (value - in);
        return value;
    }
};

// Soft-knee downward compression curve: returns gain change in dB (<= 0).
inline float compressorGainDb (float levelDb, float thresholdDb, float ratio, float kneeDb) noexcept
{
    const float over = levelDb - thresholdDb;
    const float slope = 1.0f - 1.0f / ratio;

    if (2.0f * over <= -kneeDb) return 0.0f;
    if (2.0f * over >= kneeDb)  return -slope * over;

    const float x = over + kneeDb * 0.5f;
    return -slope * x * x / (2.0f * kneeDb);
}
} // namespace moyo
