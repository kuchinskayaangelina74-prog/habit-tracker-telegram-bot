from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import yield_database_session_instance
from models import UserAccount
from schemas import (
    UserAccountCreateSchema, UserAccountResponseSchema,
    UserHabitCreateSchema, UserHabitResponseSchema,
    HabitExecutionLogCreateSchema, HabitExecutionLogResponseSchema
)
import crud
import auth

# инициализируем основное приложение FastAPI с развернутым именем переменной
app_application_instance = FastAPI(title="Habit Tracker Core API Service")
# ЭНДПОИНТЫ АУТЕНТИФИКАЦИИ И ПОЛЬЗОВАТЕЛЕЙ

@app_application_instance.post(
    "/authentication/register", 
    response_model=UserAccountResponseSchema, 
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя Telegram"
)
def register_new_user_endpoint(
    user_data_schema: UserAccountCreateSchema,
    database_session_instance: Session = Depends(yield_database_session_instance)
):
    existing_user_account = crud.find_user_account_by_telegram_id(
        database_session_instance, 
        telegram_user_identifier=user_data_schema.telegram_user_identifier
    )
    if existing_user_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким Telegram ID уже зарегистрирован в системе"
        )
    return crud.create_new_user_account(database_session_instance, user_data_schema)


@app_application_instance.post(
    "/authentication/login", 
    summary="Получение JWT-токена авторизации для бота"
)
def login_for_access_token_endpoint(
    form_data_structure: OAuth2PasswordRequestForm = Depends(),
    database_session_instance: Session = Depends(yield_database_session_instance)
):
    authenticated_user_account = crud.find_user_account_by_telegram_id(
        database_session_instance, 
        telegram_user_identifier=form_data_structure.username
    )
    
    if not authenticated_user_account or not auth.verify_user_password(
        form_data_structure.password, 
        authenticated_user_account.hashed_user_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный идентификатор Telegram или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    generated_access_token = auth.create_access_jwt_token(
        payload_data={"sub": authenticated_user_account.telegram_user_identifier}
    )
    return {"access_token": generated_access_token, "token_type": "bearer"}

# ЭНДПОИНТЫ УПРАВЛЕНИЯ ПРИВЫЧКАМИ

@app_application_instance.get(
    "/habits/list", 
    response_model=list[UserHabitResponseSchema],
    summary="Получение списка активных привычек текущего пользователя"
)
def read_user_active_habits_endpoint(
    current_authenticated_user: UserAccount = Depends(auth.get_current_authenticated_user),
    database_session_instance: Session = Depends(yield_database_session_instance)
):
    return crud.find_active_user_habits(
        database_session_instance, 
        user_account_identifier=current_authenticated_user.user_account_identifier
    )


@app_application_instance.post(
    "/habits/create", 
    response_model=UserHabitResponseSchema,
    summary="Создание новой привычки"
)
def create_user_habit_endpoint(
    habit_data_schema: UserHabitCreateSchema,
    current_authenticated_user: UserAccount = Depends(auth.get_current_authenticated_user),
    database_session_instance: Session = Depends(yield_database_session_instance)
):
    return crud.create_new_user_habit(
        database_session_instance,
        habit_data_schema,
        user_account_identifier=current_authenticated_user.user_account_identifier
    )


@app_application_instance.delete(
    "/habits/delete/{habit_identifier}", 
    response_model=UserHabitResponseSchema,
    summary="Мягкое удаление привычки"
)
def delete_user_habit_endpoint(
    habit_identifier: int,
    current_authenticated_user: UserAccount = Depends(auth.get_current_authenticated_user),
    database_session_instance: Session = Depends(yield_database_session_instance)
):
    deleted_habit_instance = crud.mark_user_habit_as_deleted(
        database_session_instance,
        habit_identifier=habit_identifier,
        user_account_identifier=current_authenticated_user.user_account_identifier
    )
    if not deleted_habit_instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Привычка не найдена или у вас нет прав на её удаление"
        )
    return deleted_habit_instance

# ЭНДПОИНТЫ ФИКСАЦИИ ВЫПОЛНЕНИЯ

@app_application_instance.post(
    "/logs/track", 
    response_model=HabitExecutionLogResponseSchema,
    summary="Фиксация прогресса выполнения"
)
def track_habit_execution_progress_endpoint(
    log_data_schema: HabitExecutionLogCreateSchema,
    current_authenticated_user: UserAccount = Depends(auth.get_current_authenticated_user),
    database_session_instance: Session = Depends(yield_database_session_instance)
):
    new_log_record = crud.create_habit_execution_log_record(
        database_session_instance,
        log_data_schema,
        user_account_identifier=current_authenticated_user.user_account_identifier
    )
    if not new_log_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось зафиксировать прогресс. Проверьте ID привычки."
        )
    return new_log_record
