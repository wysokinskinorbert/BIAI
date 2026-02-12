import reflex as rx


config = rx.Config(
    app_name="biai",
    tailwind={},
    plugins=[rx.plugins.sitemap.SitemapPlugin()],
)
