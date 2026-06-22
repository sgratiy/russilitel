# Russilitel

English loanword replacement tool for Russian text using LLM model for context-aware replacements.

## Overview

Russilitel is a Python tool that automatically replaces English loanwords in Russian text with appropriate Russian equivalents. It uses Qwen/Qwen2.5-7B-Instruct model to analyze the context and choose the most suitable replacement from a predefined list of options.

## Features

- **Context-aware replacement**: Uses LLM to understand the context and choose the best replacement
- **Multiple replacement options**: Each loanword has several Russian alternatives
- **Command-line interface**: Easy to use from terminal or scripts
- **File processing**: Can process entire files
- **Interactive mode**: Real-time text processing
- **Customizable**: Supports different models

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. The tool will automatically download the Russian BERT model on first run.

## Usage

### Basic Usage

Replace text directly from command line:
```bash
python russilitel.py "У нас дедлайн завтра по проекту"
```

### Interactive Mode

Start interactive mode for real-time processing:
```bash
python russilitel.py --interactive
```

### File Processing

Process a file and save the result:
```bash
python russilitel.py -f input.txt -o output.txt
```

### Custom Model

Use a different BERT model:
```bash
python russilitel.py --model "your-model-name" "text"
```

### From Standard Input

Process text from stdin:
```bash
echo "У нас дедлайн завтра" | python russilitel.py
```

## Loanword Dictionary

The tool currently supports these loanwords with their Russian alternatives:

- **дедлайн**: ["крайний срок", "срок сдачи", "предельный срок"]
- **фидбек**: ["отзыв", "обратная связь", "отклик"]  
- **кейс**: ["случай", "пример", "дело", "портфель"]

## How It Works

1. Detect loan words in russian text
2. Create map of loan words → English lemma (using LLM)
3. Map English lemma → proper authentic Russian word candidates (using purism dictionaries)
4. Lexical edit: choose most appropriate russian word based on context
5. Grammar edit: correct minor word ending inconsistencies (using LLM)


## Examples

### Input:
```
Давай ты пошеришь экран, а я зааппрувлю доки после митинга.
Пожалуйста, дайте мне фидбек по презентации.

```

### Output:
```
Давай ты поделишься экраном, а я проверю доки после собрания.
Пожалуйста, дайте мне обратную связь по презентации.
```

## Testing

Run the test suite to see the tool in action:
```bash
python test_russilitel.py
```

## Requirements

- Python 3.7+
- torch
- transformers
- numpy

## Performance Notes

- The first run will be slower as the BERT model needs to be downloaded
- Subsequent runs will be faster as the model is cached locally
- The tool works best with sentences containing clear context around the loanwords

## Contributing

To add new loanwords, modify the `_build_loanword_map()` method in `russilitel.py`:

```python
def _build_loanword_map(self) -> Dict[str, List[str]]:
    return {
        "new_loanword": ["russian_option1", "russian_option2", "russian_option3"],
        # ... existing entries
    }
```

## License

This project is open source and available under the MIT License.