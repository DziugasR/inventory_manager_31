from .database import get_config_session
from .models_custom import Setting


def get_setting(key: str, default: str | None = None) -> str | None:
    """
    Retrieves a setting value from the database.

    Args:
        key: The name of the setting to retrieve.
        default: The value to return if the setting is not found.

    Returns:
        The setting's value as a string, or the default value.
    """
    session = get_config_session()
    try:
        setting = session.query(Setting).filter_by(key=key).first()
        return setting.value if setting else default
    finally:
        session.close()


def set_setting(key: str, value: str):
    """
    Saves or updates a setting in the database.

    Args:
        key: The name of the setting to save.
        value: The value of the setting to save.
    """
    session = get_config_session()
    try:
        setting = session.query(Setting).filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            new_setting = Setting(key=key, value=value)
            session.add(new_setting)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"CRITICAL: Failed to set setting '{key}': {e}")
    finally:
        session.close()