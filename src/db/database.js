const path = require('path');
const Database = require('better-sqlite3');
const defaults = require('../config/defaults');

const db = new Database(path.resolve(process.cwd(), 'data.sqlite'));

function migrate() {
  db.exec(`
    CREATE TABLE IF NOT EXISTS guild_configs (
      guild_id TEXT PRIMARY KEY,
      config_json TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS registrations (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      guild_id TEXT NOT NULL,
      user_id TEXT NOT NULL,
      status TEXT NOT NULL,
      form_json TEXT NOT NULL,
      reviewer_id TEXT,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS farm_entries (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      guild_id TEXT NOT NULL,
      user_id TEXT NOT NULL,
      channel_id TEXT NOT NULL,
      farm_qtd INTEGER NOT NULL,
      powder_qtd INTEGER NOT NULL,
      capsule_qtd INTEGER NOT NULL,
      created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS hierarchy_roles (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      guild_id TEXT NOT NULL,
      role_id TEXT NOT NULL,
      position INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS hierarchy_views (
      guild_id TEXT PRIMARY KEY,
      channel_id TEXT NOT NULL,
      message_id TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS actions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      guild_id TEXT NOT NULL,
      channel_id TEXT NOT NULL,
      message_id TEXT,
      name TEXT NOT NULL,
      date TEXT NOT NULL,
      time TEXT NOT NULL,
      max_participants INTEGER NOT NULL,
      participants_json TEXT NOT NULL,
      responsible_role_id TEXT,
      created_by TEXT NOT NULL,
      created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      guild_id TEXT NOT NULL,
      type TEXT NOT NULL,
      payload_json TEXT NOT NULL,
      created_at TEXT NOT NULL
    );
  `);
}

function now() {
  return new Date().toISOString();
}

function getGuildConfig(guildId) {
  const row = db.prepare('SELECT config_json FROM guild_configs WHERE guild_id = ?').get(guildId);
  if (!row) return JSON.parse(JSON.stringify(defaults));
  const parsed = JSON.parse(row.config_json);
  return {
    ...defaults,
    ...parsed,
    visual: { ...defaults.visual, ...(parsed.visual || {}) },
    permissions: { ...defaults.permissions, ...(parsed.permissions || {}) },
    channels: { ...defaults.channels, ...(parsed.channels || {}) }
  };
}

function setGuildConfig(guildId, config) {
  db.prepare(`
    INSERT INTO guild_configs (guild_id, config_json)
    VALUES (?, ?)
    ON CONFLICT(guild_id)
    DO UPDATE SET config_json = excluded.config_json
  `).run(guildId, JSON.stringify(config));
}

function patchGuildConfig(guildId, section, key, value) {
  const config = getGuildConfig(guildId);
  config[section][key] = value;
  setGuildConfig(guildId, config);
  return config;
}

function addLog(guildId, type, payload) {
  db.prepare('INSERT INTO logs (guild_id, type, payload_json, created_at) VALUES (?, ?, ?, ?)')
    .run(guildId, type, JSON.stringify(payload), now());
}

module.exports = {
  db,
  migrate,
  now,
  getGuildConfig,
  setGuildConfig,
  patchGuildConfig,
  addLog
};
