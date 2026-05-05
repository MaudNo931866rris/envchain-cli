# envchain-cli

> Manage and inject environment variable sets per project context using encrypted local profiles.

---

## Installation

```bash
pip install envchain-cli
```

Or with [pipx](https://pypa.github.io/pipx/) (recommended):

```bash
pipx install envchain-cli
```

---

## Usage

**Create a new profile and add variables:**

```bash
envchain set myproject AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
envchain set myproject AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG
```

**Run a command with injected environment variables:**

```bash
envchain run myproject -- python deploy.py
```

**List all profiles:**

```bash
envchain list
```

**View variables in a profile:**

```bash
envchain show myproject
```

**Delete a profile:**

```bash
envchain delete myproject
```

Profiles are stored locally in an encrypted format using your system keyring. No secrets are written to plain text.

---

## How It Works

`envchain-cli` stores named environment variable sets (profiles) encrypted via your OS keyring or a local AES-encrypted vault. When you run a command with `envchain run`, the variables are injected into the subprocess environment without ever touching your shell history or `.env` files.

---

## License

This project is licensed under the [MIT License](LICENSE).