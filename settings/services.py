from .models import UserSetting, GlobalSetting, SettingType

class UserSettingService:
    @staticmethod
    def get_user_setting(user, setting_type):
        return UserSetting.objects.filter(user=user, setting_type=setting_type).first()

    @staticmethod
    def update_user_setting(user, setting_type, value):
        user_setting, created = UserSetting.objects.get_or_create(user=user, setting_type=setting_type)
        user_setting.value = value
        user_setting.save()
        return user_setting

class GlobalSettingService:
    @staticmethod
    def get_global_setting(setting_type):
        return GlobalSetting.objects.filter(setting_type=setting_type).first()

    @staticmethod
    def update_global_setting(setting_type, value):
        global_setting, created = GlobalSetting.objects.get_or_create(setting_type=setting_type)
        global_setting.value = value
        global_setting.save()
        return global_setting

class SettingTypeService:
    @staticmethod
    def get_setting_type(name):
        return SettingType.objects.filter(name=name).first()

    @staticmethod
    def create_setting_type(name, description):
        setting_type, created = SettingType.objects.get_or_create(name=name, description=description)
        return setting_type