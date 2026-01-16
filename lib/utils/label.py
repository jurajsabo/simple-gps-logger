from kivy             import platform
from kivy.properties  import NumericProperty, BooleanProperty
from kivy.core.window import Window
from kivy.metrics     import Metrics

from kivymd.material_resources import dp
from kivymd.uix.label          import MDLabel


if platform == 'android':
    from jnius import autoclass

    BuildVersion   = autoclass('android.os.Build$VERSION')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    AdSize         = autoclass('com.google.android.gms.ads.AdSize')
    DisplayMetrics = autoclass('android.util.DisplayMetrics')

    activity = PythonActivity.mActivity


class CustomLabel(MDLabel):
    '''
        A customized MDLabel that supports a `custom_font_size` property.

        This subclass extends the base `MDLabel` by adding a numeric property
        to control the font size. If provided, the font size is applied at
        initialization and can be updated dynamically.
    '''
    custom_font_size = NumericProperty(None)

    def __init__(self, **kwargs):
        '''
            Initialize the custom label and apply the custom font size if provided.
        '''
        super().__init__(**kwargs)
        self._update_font_size()

    def _update_font_size(self, *args):
        '''
            Apply the custom font size to the label if `custom_font_size` is set.
        '''
        if self.custom_font_size is not None:
            self.font_size = self.custom_font_size


class MockBanner(CustomLabel):
    """
        Kivy-side mock banner that matches AdMob Anchored Adaptive Banner height.
    """

    test = BooleanProperty(platform != 'android')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.size_hint_y = None
        self.halign      = 'center'

        # Placeholder styling (non-Android)
        if self.test:
            self.text             = '[BANNER PLACEHOLDER]'
            self.theme_text_color = 'Custom'
            self.color            = [0.7, 0.7, 0.7, 1]

        Window.bind(size = self.update_banner_height)
        self.update_banner_height()

    def update_banner_height(self, *args):
        if platform == 'android':
            self.height = self.get_adaptive_banner_height()
        else:
            self.height = self.get_mock_banner_height()

    def get_adaptive_banner_height(self):
        """
            Android: calculate height using Anchored Adaptive Banner logic.
            Mirrors real AdView sizing.
        """
        try:
            metrics = DisplayMetrics()
            activity.getWindowManager().getDefaultDisplay().getMetrics(metrics)

            width_px = metrics.widthPixels
            density  = metrics.density
            width_dp = int(width_px / density)

            ad_size = AdSize.getCurrentOrientationAnchoredAdaptiveBannerAdSize(activity, width_dp)

            banner_px = ad_size.getHeightInPixels(activity)
            height    = dp(banner_px / density)

            print('[BANNER]', f'Adaptive height: {height} dp')
            return height

        except Exception as e:
            print('[BANNER]', f'Adaptive height failed: {e}')
            return self.get_mock_banner_height()

    def get_mock_banner_height(self):
        """
            Non-Android fallback that approximates adaptive banner rules.
            Matches Google’s documented behavior.
        """
        width_dp = Window.width / Metrics.density

        if width_dp >= 728:
            banner_dp = 90        # tablet
        elif width_dp >= 468:
            banner_dp = 60        # large phone / landscape
        else:
            banner_dp = 50        # phone portrait

        height = dp(banner_dp)
        print('[BANNER]', f'Mock height: {height} dp')
        return height


class MockNavigationBar(CustomLabel):
    test = BooleanProperty(platform != 'android')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.halign      = 'center'

        # Placeholder
        if self.test:
            self.text             = '[NAVIGATION BAR PLACEHOLDER]'
            self.theme_text_color = 'Custom'
            self.color            = [0.7, 0.7, 0.7, 1]

        Window.bind(size = self.update_navigation_height)
        self.update_navigation_height()

    def update_navigation_height(self, *args):
        if platform == 'android':
            self.height = self.get_navigation_bar_height()
        else:
            self.height = 0

    def get_navigation_bar_height(self):
        try:
            SDK_INT = int(BuildVersion.SDK_INT)

            # Only need manual offset handling for API 35+
            if SDK_INT >= 35:
                try:
                    decor_view = activity.getWindow().getDecorView()
                    insets     = decor_view.getRootWindowInsets()

                    if insets is None:
                        return 0

                    density          = activity.getResources().getDisplayMetrics().density
                    WindowInsetsType = autoclass('android.view.WindowInsets$Type')
                    px               = insets.getInsets(WindowInsetsType.navigationBars()).bottom

                    height = dp(px / density)
                    print('[NAV BAR]', f'height: {height} dp')
                    return height

                except Exception as e:
                    print(f'[NAV BAR] Error: {e}')
                    return 0
            else:
                # API < 35: system handles it automatically
                return 0

        except Exception as e:
            print('[NAV BAR]', e)
            return 0
