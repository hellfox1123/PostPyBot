    async def init(self, bot=None):
        """Ініціалізація клієнта з детальною діагностикою"""
        self.bot = bot
        
        session_file = f"{SESSION_PATH}.session"
        logger.info(f"=== ДІАГНОСТИКА ===")
        logger.info(f"API_ID: {API_ID}")
        logger.info(f"API_HASH: {API_HASH[:10]}...")
        logger.info(f"SESSION_PATH: {SESSION_PATH}")
        logger.info(f"Файл: {session_file}")
        
        if not os.path.exists(session_file):
            logger.error(f"❌ Файл НЕ знайдено!")
            return False
        
        file_size = os.path.getsize(session_file)
        logger.info(f"✅ Файл знайдено ({file_size} байт)")
        
        self.client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
        
        try:
            await self.client.connect()
            logger.info("✅ Підключено до Telegram серверів")
            
            # Спробуємо отримати дані користувача
            try:
                me = await self.client.get_me()
                logger.info(f"✅ АВТОРИЗОВАНО як @{me.username} (ID: {me.id})")
                return True
            except Exception as auth_error:
                logger.error(f"❌ Сесія невалідна: {type(auth_error).__name__}: {auth_error}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Помилка підключення: {type(e).__name__}: {e}")
            return False
