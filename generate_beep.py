#!/usr/bin/env python3
"""Generate a simple beep audio file for alert"""
import wave
import math
import struct

def generate_beep(filename='alarm.wav', duration=5.0, frequency=800):
    """Generate a beep sound file"""
    sample_rate = 44100
    num_samples = int(sample_rate * duration)

    # Generate sine wave
    samples = []
    for i in range(num_samples):
        # Create a beep sound with fade in/out to avoid clicks
        t = i / sample_rate
        fade = 1.0
        if t < 0.01:  # Fade in
            fade = t / 0.01
        elif t > duration - 0.01:  # Fade out
            fade = (duration - t) / 0.01

        # Generate tone
        value = fade * math.sin(2 * math.pi * frequency * t)

        # Convert to 16-bit PCM
        sample = int(32767 * value)
        samples.append(sample)

    # Write WAV file
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        # Write samples
        for sample in samples:
            wav_file.writeframes(struct.pack('<h', sample))

    print(f"Generated {filename}: {duration}s at {frequency}Hz")

if __name__ == '__main__':
    # Generate a 5-second beep sound
    generate_beep('alarm.wav', duration=5.0, frequency=800)
    print("Audio file created successfully!")
