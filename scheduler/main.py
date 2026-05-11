import sys
import os
from datetime import datetime, date
from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))
from models import UserHabit, HabitExecutionLog

DATABASE_POSTGRES_CONNECTION_URL = "postgresql://habits_admin:secure_password_123@localhost:5432/habits_tracking_db"

database_engine_instance = create_engine(DATABASE_POSTGRES_CONNECTION_URL)
DatabaseSessionLocalFactory = sessionmaker(autocommit=False, autoflush=False, bind=database_engine_instance)


def execute_daily_habit_transfer_and_archiving_job():
    print(f"[{datetime.now()}] Запуск фоновой проверки...")
    database_session_instance = DatabaseSessionLocalFactory()
    current_date_object = date.today()
    
    try:
        active_habits_list = database_session_instance.query(UserHabit).filter(
            UserHabit.is_habit_deleted_status == False
        ).all()
        
        for habit_item in active_habits_list:
            today_execution_log = database_session_instance.query(HabitExecutionLog).filter(
                HabitExecutionLog.target_habit_foreign_key == habit_item.habit_identifier,
                HabitExecutionLog.habit_execution_date == current_date_object
            ).first()
            
            if not today_execution_log:
                failed_log_record_instance = HabitExecutionLog(
                    target_habit_foreign_key=habit_item.habit_identifier,
                    habit_execution_date=current_date_object,
                    is_habit_completed_successfully=False
                )
                database_session_instance.add(failed_log_record_instance)
            
            if habit_item.total_execution_success_count >= 21:
                habit_item.is_habit_deleted_status = True
                print(f"Привычка ID {habit_item.habit_identifier} успешно завершила цикл и отправлена в архив.")
                
        database_session_instance.commit()
        print("Фоновое обновление статусов привычек успешно завершено.")
        
    except Exception as unexpected_error_object:
        database_session_instance.rollback()
        print(f"Произошла критическая ошибка при обновлении: {unexpected_error_object}")
    finally:
        database_session_instance.close()


if __name__ == "__main__":
    scheduler_application_instance = BlockingScheduler()

    scheduler_application_instance.add_job(
        execute_daily_habit_transfer_and_archiving_job, 
        'cron', 
        hour=0, 
        minute=0
    )
    
    print("Фоновый планировщик успешно запущен и ожидает наступления полуночи...")
    try:
        scheduler_application_instance.start()
    except (KeyboardInterrupt, SystemExit):
        print("Фоновый планировщик успешно остановлен.")
