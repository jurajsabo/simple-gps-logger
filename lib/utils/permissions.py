from android.permissions import request_permissions, Permission
from jnius               import autoclass

Build_VERSION = autoclass('android.os.Build$VERSION')

class PermissionsManager:
    '''
        Manages Android runtime permissions with sequential requests.
        Each permission waits to be granted before the next one is requested.
        Individual callbacks can be defined for each permission.
    '''

    def __init__(self, app):
        self.app                = app
        self.permissions_config = []
        self.current_index      = 0

    def _setup_permissions(self):
        '''
            Configure all required permissions
        '''
        SDK_INT = int(Build_VERSION.SDK_INT)

        self.add_permission \
        (
            Permission.ACCESS_FINE_LOCATION,
            on_granted = self.app.on_location_granted,
            on_denied  = self.app.on_location_denied
        )

        # Notification permission (API 33+)
        if SDK_INT >= 33:
            self.add_permission \
            (
                Permission.POST_NOTIFICATIONS,
                on_granted = self.app.on_notifications_granted,
                on_denied  = self.app.on_notifications_denied
            )

        # Storage permissions (API 23-29)
        if 23 <= SDK_INT <= 29:
            self.add_permission \
            (
                Permission.WRITE_EXTERNAL_STORAGE,
                on_granted = self.app.on_storage_granted,
                on_denied  = self.app.on_storage_denied
            )

    def add_permission(self, permission, on_granted = None, on_denied = None):
        '''
            Add a permission to the request queue.

            Args:
                permission: The permission constant (e.g., Permission.ACCESS_FINE_LOCATION)
                on_granted: Callback function when permission is granted
                on_denied: Callback function when permission is denied
        '''
        self.permissions_config.append \
        (
            {
                'permission': permission,
                'on_granted': on_granted,
                'on_denied':  on_denied
            }
        )

    def request_permissions(self):
        '''
            Start requesting permissions sequentially.
            Call this method after adding all permissions.
        '''
        self._setup_permissions()
        self.current_index = 0
        self._request_next_permission()

    def _request_next_permission(self):
        '''
            Internal method to request the next permission in the queue.
        '''
        if self.current_index >= len(self.permissions_config):
            self.on_all_permissions_complete()

        else:
            # Get current permission configuration
            config = self.permissions_config[self.current_index]
            current_permission = [config['permission']]

            # Request permission with callback
            request_permissions(current_permission, self._permission_callback)

    def _permission_callback(self, permissions, results):
        '''
            Internal callback fired when a permission request is completed.

            Args:
                permissions: List of permissions that were requested
                results: List of boolean results for each permission
        '''
        config = self.permissions_config[self.current_index]

        for permission, result in zip(permissions, results):
            if result:
                print('[PERMISSION]', f'{permission}: granted')
                # Execute the specific granted callback for this permission
                if config['on_granted']:
                    config['on_granted']()
            else:
                print('[PERMISSION]', f'{permission}: denied')
                # Execute the specific denied callback for this permission
                if config['on_denied']:
                    config['on_denied']()

        # Request next permission regardless of result
        self.current_index += 1
        self._request_next_permission()

    def on_all_permissions_complete(self):
        '''
            Called when all permissions have been processed.
        '''
        if self.app and hasattr(self.app, 'on_all_permissions_complete'):
            self.app.on_all_permissions_complete()
        else:
            print('[APP] Permission flow complete - App ready!')
