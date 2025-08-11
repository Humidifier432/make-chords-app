# make_music_chords.py

import os
import re
from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo

def generate_music(filename, input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    key_sharp = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    processed_data = []

    TICKS_PER_BEAT = 480
    NOTE_DURATION = 4 * TICKS_PER_BEAT
    BPM = 120

    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()

            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if ":" in line:
                    _, content = line.split(":", 1)
                else:
                    content = line

                words = content.strip().split()
                cleaned_words = []

                for word in words:
                    if "/" in word:
                        word = re.sub(r"/.*?♭", "", word)
                    if word.endswith("M"):
                        word = word[:-1]
                    cleaned_words.append(word)

                processed_data.append(cleaned_words)

        for idx, chord_list in enumerate(processed_data, 1):
            merged_midi = MidiFile(ticks_per_beat=TICKS_PER_BEAT)
            merged_track = MidiTrack()
            merged_midi.tracks.append(merged_track)
            merged_track.append(MetaMessage('set_tempo', tempo=bpm2tempo(BPM), time=0))

            for chord in chord_list:
                sorted_keys = sorted(key_sharp, key=lambda x: -len(x))
                key = next((k for k in sorted_keys if chord.startswith(k)), None)
                if not key:
                    print(f"Warning: No matching key found for {chord}. Skipping.")
                    continue

                chord_path = os.path.join(input_folder, key, f"{chord}.mid")
                if not os.path.exists(chord_path):
                    print(f"Warning: File not found: {chord_path}")
                    continue

                try:
                    midi = MidiFile(chord_path)
                    notes_on = []
                    notes_off = []

                    for track in midi.tracks:
                        abs_time = 0
                        for msg in track:
                            abs_time += msg.time
                            if msg.type == 'note_on' and msg.velocity > 0:
                                notes_on.append((abs_time, msg.note, msg.velocity))
                            elif msg.type in ('note_off', 'note_on') and msg.velocity == 0:
                                notes_off.append((abs_time, msg.note))

                    active_notes = set(note for _, note, _ in notes_on)
                    print(f"chord: {chord} - active_notes: {active_notes}")

                    for i, note in enumerate(sorted(active_notes)):
                        merged_track.append(Message('note_on', note=note, velocity=64, time=0 if i == 0 else 0))
                    merged_track.append(Message('note_off', note=sorted(active_notes)[0], velocity=64, time=NOTE_DURATION))
                    for note in sorted(active_notes)[1:]:
                        merged_track.append(Message('note_off', note=note, velocity=64, time=0))

                except Exception as e:
                    print(f"Error: An issue occurred while loading {chord_path}: {e}")

            if len(merged_track) > 1:
                output_path = os.path.join(output_folder, f"set{idx}.mid")
                merged_midi.save(output_path)
                print(f"✅ Saved set {idx} to {output_path}.")

    except FileNotFoundError:
        print(f"{filename} not found. Did you save the file?")
