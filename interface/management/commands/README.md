# Django Management Commands

## generate_questions

The `generate_questions` command allows you to generate new questions for your Code Checker application using the OpenAI API.

### Usage

```bash
python manage.py generate_questions [options]
```

### Options

- `--coding <number>`: Number of coding questions to generate for each language and level.
- `--theory <number>`: Number of theory questions to generate for each language and level.
- `--mcq <number>`: Number of MCQ questions to generate for each language and level.
- `--all <number>`: Generate equal number of all question types for each language and level.
- `--language <id|all>`: Specific language ID or "all" for all languages.
- `--level <id|all>`: Specific level ID or "all" for all levels.
- `--openai-key <key>`: OpenAI API key to use (optional, uses settings.OPENAI_API_KEY if not provided).

### Examples

Generate 1 question of each type for all languages and levels:
```bash
python manage.py generate_questions --all 1
```

Generate 5 coding questions for all languages and levels:
```bash
python manage.py generate_questions --coding 5
```

Generate 3 theory questions and 2 MCQs for a specific language (ID=2) and level (ID=1):
```bash
python manage.py generate_questions --theory 3 --mcq 2 --language 2 --level 1
```

### Notes

- The command uses the OpenAI API to generate questions, so make sure your API key is configured.
- Questions are stored in the database and can be accessed through the admin interface.
- The command will report progress and any errors that occur during generation.
- For each language-level combination, the specified number of questions will be generated.

### Requirements

- OpenAI API key (set in .env file or passed via --openai-key option)
- Django admin user (created automatically if not exists) 