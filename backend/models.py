from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date
from sqlalchemy.orm import declarative_base, relationship

DatabaseDeclarativeBase = declarative_base()

class UserAccount(DatabaseDeclarativeBase):
    __tablename__ = "user_accounts"

    user_account_identifier = Column(Integer, primary_key=True, index=True)
    telegram_user_identifier = Column(String, unique=True, index=True, nullable=False)
    hashed_user_password = Column(String, nullable=False)

    user_habits_collection = relationship("UserHabit", back_populates="habit_owner_account")


class UserHabit(DatabaseDeclarativeBase):
    __tablename__ = "user_habits"
    
    habit_identifier = Column(Integer, primary_key=True, index=True)
    habit_title_name = Column(String, nullable=False)

    total_execution_success_count = Column(Integer, default=0)
    is_habit_deleted_status = Column(Boolean, default=False)

    owner_account_foreign_key = Column(Integer, ForeignKey("user_accounts.user_account_identifier"))

    habit_owner_account = relationship("UserAccount", back_populates="user_habits_collection")
    habit_execution_logs_collection = relationship("HabitExecutionLog", back_populates="target_user_habit")


class HabitExecutionLog(DatabaseDeclarativeBase):
    __tablename__ = "habit_execution_logs"
    
    log_record_identifier = Column(Integer, primary_key=True, index=True)
    target_habit_foreign_key = Column(Integer, ForeignKey("user_habits.habit_identifier"))
    
    habit_execution_date = Column(Date, nullable=False)
    is_habit_completed_successfully = Column(Boolean, default=False)
    
    target_user_habit = relationship("UserHabit", back_populates="habit_execution_logs_collection")