from kivymd.uix.screen     import MDScreen
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.boxlayout  import MDBoxLayout

from lib.utils.about  import about_text
from lib.utils.banner import BannerAd
from lib.utils.label  import CustomLabel, MockBanner


class AboutScreen(MDScreen, BannerAd):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print('[ABOUT]', 'init')

        # Main layout
        main_layout = MDBoxLayout(orientation = 'vertical', spacing = 0)

        # Mock banner
        self.mock_banner = MockBanner()

        # ---- Set up AdMob -----
        self.ad_create()
        self.ad_show()

        # Remaining layout
        main_layout.add_widget(self.mock_banner)
        main_layout.add_widget \
        (
            MDScrollView \
            (
                CustomLabel \
                (
                    text        = about_text,
                    markup      = True,  # enable BBCode-style formatting
                    halign      = "left",
                    valign      = "top",
                    padding     = [20, 20],
                    size_hint_y = None
                )

            )

        )
        # Add the main layout to screen
        self.add_widget(main_layout)

        # Get label reference
        scroll_view = None
        for child in main_layout.children:
            if isinstance(child, MDScrollView):
                scroll_view = child
                break

        if scroll_view:
            label = scroll_view.children[0]
            # Bind the label's texture_size to its height, so it sizes properly
            label.bind(texture_size = label.setter('size'))

    def on_size(self, *args):
        self.mock_banner.update_banner_height()
