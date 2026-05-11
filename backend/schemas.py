from datetime import date
from pydantic import BaseModel, Field

# СХЕМЫ ДЛЯ УЧЕТНЫХ ЗАПИСЕЙ ПОЛЬЗОВАТЕЛЕЙ

class UserAccountBaseSchema(BaseModel):
    telegram_user_identifier: str = Field(..., description="Уникальный ID пользователя из Telegram")

class UserAccountCreateSchema(UserAccountBaseSchema):
    plain_text_user_password: str = Field(..., min_length=6, description="Пароль пользователя до хеширования")

class UserAccountResponseSchema(UserAccountBaseSchema):
    user_account_identifier: int

    class Config:
        #режим совместимости с ORM SQLAlchemy
        from_attributes = True


# СХЕМЫ ДЛЯ ТРЕКИНГА ПРИВЫЧЕК

class UserHabitBaseSchema(BaseModel):
    habit_title_name: str = Field(..., min_length=2, description="Название формируемой привычки")

class UserHabitCreateSchema(UserHabitBaseSchema):
    pass

class UserHabitResponseSchema(UserHabitBaseSchema):
    habit_identifier: int
    total_execution_success_count: int
    is_habit_deleted_status: bool
    owner_account_foreign_key: int

    class Config:
        from_attributes = True


# СХЕМЫ ДЛЯ ЛОГОВ ВЫПОЛНЕНИЯ ПРИВЫЧЕК

class HabitExecutionLogBaseSchema(BaseModel):
    habit_execution_date: date
    is_habit_completed_successfully: bool

class HabitExecutionLogCreateSchema(HabitExecutionLogBaseSchema):
    target_habit_foreign_key: int

class HabitExecutionLogResponseSchema(HabitExecutionLogBaseSchema):
    log_record_identifier: int
    target_habit_foreign_key: int

    class Config:
        from_attributes = True
