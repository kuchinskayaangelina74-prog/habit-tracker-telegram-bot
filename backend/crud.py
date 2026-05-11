from datetime import date
from sqlalchemy.orm import Session
from models import UserAccount, UserHabit, HabitExecutionLog
from schemas import UserAccountCreateSchema, UserHabitCreateSchema, HabitExecutionLogCreateSchema
from auth import calculate_password_hash

# БИЗНЕС-ЛОГИКА ДЛЯ ПОЛЬЗОВАТЕЛЕЙ

def find_user_account_by_telegram_id(database_session: Session, telegram_user_identifier: str):
    return database_session.query(UserAccount).filter(
        UserAccount.telegram_user_identifier == telegram_user_identifier
    ).first()


def create_new_user_account(database_session: Session, user_data_schema: UserAccountCreateSchema):
    hashed_password_string = calculate_password_hash(user_data_schema.plain_text_user_password)
    
    new_user_account_instance = UserAccount(
        telegram_user_identifier=user_data_schema.telegram_user_identifier,
        hashed_user_password=hashed_password_string
    )
    
    database_session.add(new_user_account_instance)
    database_session.commit()
    database_session.refresh(new_user_account_instance)
    return new_user_account_instance


# БИЗНЕС-ЛОГИКА ДЛЯ ПРИВЫЧЕК

def find_active_user_habits(database_session: Session, user_account_identifier: int):
    return database_session.query(UserHabit).filter(
        UserHabit.owner_account_foreign_key == user_account_identifier,
        UserHabit.is_habit_deleted_status == False
    ).all()


def create_new_user_habit(
    database_session: Session, 
    habit_data_schema: UserHabitCreateSchema, 
    user_account_identifier: int
):
    new_habit_instance = UserHabit(
        habit_title_name=habit_data_schema.habit_title_name,
        total_execution_success_count=0,
        is_habit_deleted_status=False,
        owner_account_foreign_key=user_account_identifier
    )
    
    database_session.add(new_habit_instance)
    database_session.commit()
    database_session.refresh(new_habit_instance)
    return new_habit_instance


def mark_user_habit_as_deleted(database_session: Session, habit_identifier: int, user_account_identifier: int):
    target_habit_instance = database_session.query(UserHabit).filter(
        UserHabit.habit_identifier == habit_identifier,
        UserHabit.owner_account_foreign_key == user_account_identifier
    ).first()
    
    if target_habit_instance:
        target_habit_instance.is_habit_deleted_status = True
        database_session.commit()
        database_session.refresh(target_habit_instance)
    return target_habit_instance


def create_habit_execution_log_record(
    database_session: Session, 
    log_data_schema: HabitExecutionLogCreateSchema, 
    user_account_identifier: int
):
    # проверяем, принадлежит ли привычка текущему пользователю
    target_habit_instance = database_session.query(UserHabit).filter(
        UserHabit.habit_identifier == log_data_schema.target_habit_foreign_key,
        UserHabit.owner_account_foreign_key == user_account_identifier
    ).first()
    
    if not target_habit_instance:
        return None

    # создаем запись лога выполнения
    new_log_record_instance = HabitExecutionLog(
        target_habit_foreign_key=log_data_schema.target_habit_foreign_key,
        habit_execution_date=log_data_schema.habit_execution_date,
        is_habit_completed_successfully=log_data_schema.is_habit_completed_successfully
    )
    database_session.add(new_log_record_instance)
    
    if log_data_schema.is_habit_completed_successfully:
        target_habit_instance.total_execution_success_count += 1
        
        if target_habit_instance.total_execution_success_count >= 21:
            target_habit_instance.is_habit_deleted_status = True
            
    database_session.commit()
    database_session.refresh(new_log_record_instance)
    return new_log_record_instance
