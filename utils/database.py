import aiosqlite

DB_NAME = "database.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # Guild configuration
        await db.execute("""
            CREATE TABLE IF NOT EXISTS guild_config (
                guild_id INTEGER PRIMARY KEY,
                log_channel_id INTEGER,
                approve_role_id INTEGER,
                register_role_id INTEGER,
                farm_category_id INTEGER,
                farm_allowed_roles TEXT
            )
        """)
        
        # Bot customization (Phase 2)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bot_customization (
                guild_id INTEGER PRIMARY KEY,
                registration_color TEXT DEFAULT '#00FF00',
                farm_color TEXT DEFAULT '#FFD700',
                action_color TEXT DEFAULT '#FF0000',
                hierarchy_color TEXT DEFAULT '#8B0000',
                stats_color TEXT DEFAULT '#3498DB',
                emoji_success TEXT DEFAULT '✅',
                emoji_error TEXT DEFAULT '❌',
                emoji_farm TEXT DEFAULT '🚜',
                emoji_action TEXT DEFAULT '⚔️'
            )
        """)
        
        # Registration system
        await db.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                user_id INTEGER PRIMARY KEY,
                status TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Farm system with enhanced tracking
        await db.execute("""
            CREATE TABLE IF NOT EXISTS farms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                guild_id INTEGER,
                channel_id INTEGER,
                farm_amount INTEGER,
                powder_amount INTEGER,
                capsule_amount INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for farm queries (Phase 3 - Ranking)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_farms_user ON farms(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_farms_guild ON farms(guild_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_farms_timestamp ON farms(timestamp)")
        
        # Hierarchy system
        await db.execute("""
            CREATE TABLE IF NOT EXISTS hierarchy (
                role_id INTEGER,
                guild_id INTEGER,
                position INTEGER,
                PRIMARY KEY (role_id, guild_id)
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS hierarchy_messages (
                guild_id INTEGER PRIMARY KEY,
                channel_id INTEGER,
                message_id INTEGER
            )
        """)
        
        # Actions system
        await db.execute("""
            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                date TEXT,
                time TEXT,
                max_participants INTEGER,
                created_by INTEGER,
                message_id INTEGER,
                channel_id INTEGER,
                guild_id INTEGER
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS action_participants (
                action_id INTEGER,
                user_id INTEGER,
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (action_id, user_id),
                FOREIGN KEY (action_id) REFERENCES actions(id) ON DELETE CASCADE
            )
        """)
        
        # Advanced logging system (Phase 6)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS action_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                action_type TEXT,
                user_id INTEGER,
                target_id INTEGER,
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Ranking reset tracking
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ranking_resets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                reset_type TEXT,
                reset_by INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.commit()
        print("[DB] All tables created/verified successfully")

async def get_db():
    return await aiosqlite.connect(DB_NAME)
