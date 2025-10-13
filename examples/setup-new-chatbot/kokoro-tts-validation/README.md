# Kokoro TTS Validation

This validation suite tests the performance and functionality of the dora-kokoro-tts Text-to-Speech node with multi-language support.

## Overview

The validation measures:
- TTS synthesis time for text input
- Real-time factor (RTF) - ratio of audio duration to processing time
- Character processing speed
- Audio quality and file size
- Support for multiple languages (English, Chinese, Japanese, Korean)

## Quick Start

### 1. Install Dependencies

```bash
# Install kokoro-tts with Chinese support
pip install -e ../../../node-hub/dora-kokoro-tts
```

### 2. Direct TTS Test (Recommended)

Test TTS performance without Dora dataflow:

```bash
cd examples/setup-new-chatbot/kokoro-tts-validation

# Test English (default)
python test_tts_direct.py

# Test Chinese
python test_tts_direct.py --language zh

# Test with custom text
python test_tts_direct.py --text "Hello, this is a test!"

# Test with different voice
python test_tts_direct.py --voice bf_emma
```

This will:
- Initialize the Kokoro TTS engine
- Generate audio from the test text
- Save audio to `tts_output/kokoro_{language}_output.wav`
- Display timing metrics

### 3. Dataflow Test

Test with full Dora dataflow pipeline:

```bash
# Kill any existing Dora instances
dora destroy

# Start the dataflow
dora up
dora start dataflow-static.yml

# The dataflow will run and save audio to tts_output/kokoro_test_output.wav
# Press Ctrl+C to stop after audio generation completes
```

This runs:
- Text sender → Kokoro TTS → Audio recorder
- Saves audio to `tts_output/kokoro_test_output.wav`

### 4. Run All Tests

```bash
# Run both direct test and dataflow test
./run_all_tests.sh
```

## Test Text

### English (Default)
```
Artificial intelligence is revolutionizing the way we interact with technology. From voice assistants to autonomous vehicles, AI systems are becoming increasingly sophisticated. Machine learning algorithms can now process vast amounts of data, recognize patterns, and make decisions with remarkable accuracy.
```

### Chinese
```
我们说中国式现代化是百年大战略，这又分为三个阶段。第一个阶段，我们先用30年时间建成了独立完整的工业体系和国民经济体系；再用40年，到2021年，全面建成了小康社会。我们现在正处于第三个阶段，这又被分成上下两篇：上半篇是到2035年基本实现社会主义现代化；下半篇是到本世纪中叶，也就是2050年，建成社会主义现代化强国。
```

## Directory Structure

```
kokoro-tts-validation/
├── README.md                          # This documentation
├── test_tts_direct.py                 # Standalone TTS test (no dataflow)
├── dataflow-static.yml                # Dora dataflow configuration
├── simple_text_sender_static.py       # Text sender node
├── audio_recorder_static.py           # Audio recorder node
├── run_all_tests.sh                   # Run all tests
└── tts_output/                        # Generated audio files
    ├── kokoro_en_output.wav           # English output
    ├── kokoro_zh_output.wav           # Chinese output
    ├── kokoro_test_output.wav         # Dataflow test output
    └── kokoro_timing_results.json     # Performance metrics
```

## Configuration

### Available Voices

Kokoro TTS supports various voices. Some examples:
- `af_heart` - Female voice
- `bf_emma` - Female voice
- `am_adam` - Male voice
- `bm_lewis` - Male voice

See [Kokoro documentation](https://github.com/remsky/Kokoro-TTS) for full list.

### Language Support

| Language | Code | Kokoro Code |
|----------|------|-------------|
| English  | `en` | `a` |
| Chinese  | `zh` | `z` |
| Japanese | `ja` | `j` |
| Korean   | `ko` | `k` |

### Environment Variables

```bash
# Language setting (for dataflow test)
export LANGUAGE=en  # en, zh, ja, ko
```

## Performance Expectations

Kokoro TTS is designed for fast inference:

| Metric | Typical Value |
|--------|---------------|
| Real-time Factor | 5-20x (CPU) |
| Processing Speed | 50-200 chars/sec |
| Sample Rate | 24000 Hz |
| Audio Quality | High quality |

**Note**: Actual performance depends on:
- CPU/GPU capabilities
- Text length and complexity
- Language being synthesized
- Voice model selected

## Comparison with PrimeSpeech

| Feature | Kokoro TTS | PrimeSpeech |
|---------|------------|-------------|
| **Languages** | EN, ZH, JA, KO | ZH, EN |
| **Speed (RTF)** | 5-20x (fast) | 0.7-2x (slower) |
| **Quality** | Good | Excellent |
| **Voices** | Multiple built-in | Custom cloned voices |
| **Setup** | Simple pip install | Requires model downloads |
| **Use Case** | General purpose | Voice cloning, custom voices |
| **Streaming** | Yes (via generator) | Yes (configurable) |
| **Dependencies** | Minimal | Heavy (PyTorch, transformers) |

## Troubleshooting

### Common Issues

1. **Import Error: No module named 'kokoro'**
   ```bash
   pip install kokoro>=0.2.2
   ```

2. **Chinese Characters Not Working**
   ```bash
   # Install Chinese support
   pip install "misaki[zh]"
   ```

3. **Audio Quality Issues**
   - Try different voices with `--voice` parameter
   - Ensure text is in the correct language
   - Check sample rate matches playback device

4. **Slow Performance**
   - Kokoro is CPU-optimized, should be fast
   - Check system resources (CPU usage, memory)
   - Try shorter text segments

## Testing Different Languages

### English
```bash
python test_tts_direct.py --language en --text "Hello world"
```

### Chinese
```bash
python test_tts_direct.py --language zh --text "你好世界"
```

### Mixed Language (Auto-detect)
```bash
# Kokoro auto-detects Chinese characters
python test_tts_direct.py --language en --text "Hello 你好"
```

## Dependencies

- Python 3.8+
- dora-kokoro-tts
- kokoro>=0.2.2
- soundfile>=0.13.1
- misaki[zh] (for Chinese support)
- NumPy
- PyArrow

## Performance Benchmarking

To benchmark performance:

```bash
# Run direct test and note metrics
python test_tts_direct.py --language en

# Expected output:
# - Real-time factor: 10-20x (should be > 1.0)
# - Processing speed: 100+ characters/second
# - Audio duration vs synthesis time
```

## Integration with Dora Pipeline

Kokoro TTS can be integrated into voice chatbot pipelines:

```yaml
nodes:
  - id: kokoro-tts
    path: dora-kokoro-tts
    inputs:
      text: llm/response
    outputs:
      - audio
    env:
      LANGUAGE: en
```

The simple interface makes it easy to use:
- **Input**: `text` (string)
- **Output**: `audio` (float array) with `sample_rate` metadata

## License

See main Dora project license.

## Support

For issues specific to:
- **Kokoro TTS**: https://github.com/remsky/Kokoro-TTS
- **Dora Framework**: https://github.com/kippalbot/dora
