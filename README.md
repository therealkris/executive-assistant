# executive-assistant-plugin

A Claude Code plugin marketplace containing one plugin.

| Plugin | What it does |
|---|---|
| [`executive-assistant`](plugins/executive-assistant/) | Recurring executive-assistant automations as skills — inbox triage, daily and weekly briefings, meeting prep and note ingest, voice profile, relationship CRM, receipt forwarding |

## Install

```
/plugin marketplace add therealkris/executive-assistant-plugin
/plugin install executive-assistant@executive-assistant-plugin
```

Then, in any Claude session, say **"set up"**. The plugin's `setup` skill detects which tools you have
connected, asks a few multiple-choice questions, and writes your configuration for you — no file
editing, no paths to type. See the plugin's own
[README](plugins/executive-assistant/README.md) for details.

Nothing here assumes you have a particular set of tools. Each skill declares which capabilities it
requires and which are optional, and anything unconfigured is skipped rather than failing — so
someone with only email connected still gets working inbox triage and an email-only briefing.

### Installing from a fork or a local clone

You don't need this marketplace. Two alternatives:

- **Your own fork** — `/plugin marketplace add <your-owner>/<your-repo>`, then
  `/plugin install executive-assistant@<the name in your marketplace.json>`.
- **No marketplace at all** — copy or symlink `plugins/executive-assistant/` into your Claude skills
  directory. Any folder there containing `.claude-plugin/plugin.json` loads on the next session with
  no install step.

## Distributing to a team

If you want everyone in an organization on the same version, there are three tiers, weakest to
strongest.

**1. Per-repo prompt.** Add to a project's `.claude/settings.json`. Team members are prompted to
install when they trust the folder:

```json
{
  "extraKnownMarketplaces": {
    "executive-assistant-plugin": {
      "source": { "source": "github", "repo": "therealkris/executive-assistant-plugin" }
    }
  },
  "enabledPlugins": {
    "executive-assistant@executive-assistant-plugin": true
  }
}
```

**2. Managed settings.** The same two keys in `managed-settings.json` register the marketplace
automatically — no `/plugin marketplace add` needed — and users can't override it. Pair with
`strictKnownMarketplaces` to allowlist only approved sources:

```json
{
  "strictKnownMarketplaces": [
    { "source": "github", "repo": "therealkris/executive-assistant-plugin" }
  ]
}
```

Note that `strictKnownMarketplaces` only *restricts* what can be added; it does not register
anything. It needs `extraKnownMarketplaces` alongside it to auto-register. An empty array `[]` is a
full lockdown that blocks even the official Anthropic marketplace.

**3. Organization settings** (Team/Enterprise plans) — admin-managed sync at
Organization settings → Plugins on claude.ai. This path does not use anyone's git credentials; it
reads the repo through the Claude GitHub App. Constraints worth knowing:

- The marketplace repo must be owned by the organization, and **private or internal**. Org sync does
  not distribute a public repo you don't own, so to use this tier, fork this repo into your org and
  make the fork internal.
- Plugin sources may be `github`, `url`, or `git-subdir`. **`npm` sources are not supported.**
- A *private* plugin source only works if it shares the marketplace repo's owner. Everything else
  must be public.

That last constraint is why `executive-assistant` lives inside this repo and is referenced by
relative path (`./plugins/executive-assistant`) rather than as a separate repo — a fork stays
self-contained, and users never need access to a second repository.

### Private forks and git credentials

Tiers 1 and 2 clone the marketplace with your **existing git credentials**; there is no private-repo
flag. None of this applies to a public marketplace, but if you fork into a private repo, two things
are worth knowing:

- GitHub `owner/repo` shorthand clones over **SSH** by default. Set
  `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` to use HTTPS instead.
- Background auto-updates disable git credential helpers, so **HTTPS background pulls can't
  authenticate to a private repo.** SSH remotes with a key in `ssh-agent` work fine. On HTTPS, the
  failed pull falls back to a full re-clone, which can time out. Set
  `CLAUDE_CODE_PLUGIN_KEEP_MARKETPLACE_ON_FAILURE=1` to keep the existing clone instead of
  re-cloning, and run `gh auth setup-git` so the fallback can authenticate without prompting.

## Adding another plugin

1. Create `plugins/<name>/` with a `.claude-plugin/plugin.json`.
2. Add an entry to `.claude-plugin/marketplace.json` with `"source": "./plugins/<name>"`.
3. Run `claude plugin validate .` from the repo root.

Keep `plugins/<name>/.claude-plugin/plugin.json` free of a `version` field. Without it, every commit
counts as a new version and updates flow automatically. If you add `version`, the plugin is **pinned**
to that string — pushing new commits does nothing for anyone who already installed it until you bump
the field. Never set `version` in both `plugin.json` and the marketplace entry; the `plugin.json`
value silently wins.

A plugin's `name` is its stable identifier — it appears in `enabledPlugins` and install commands.
To relabel without breaking installs, add `displayName` and leave `name` alone. To actually rename,
use the marketplace's `renames` map so existing installs migrate.

## Validate

```
claude plugin validate .                              # marketplace + local plugin entries
claude plugin validate ./plugins/executive-assistant  # one plugin's manifest and skill frontmatter
```

## License

MIT — see [LICENSE](LICENSE).
