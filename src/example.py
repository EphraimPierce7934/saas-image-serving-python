import os

from saas_image_service import ImageRequest, ImageServingService, InfraiClient, Tenant


def main() -> None:
    tenant = Tenant("acme", "Acme Analytics", active=True)
    image = ImageRequest(tenant.tenant_id, "dashboard.png", b"example image bytes")
    result = ImageServingService(InfraiClient(os.environ.get("INFRAI_API_KEY"))).optimize_for_serving(tenant, image)
    print({"tenant": tenant.tenant_id, "compressed_image": result})


if __name__ == "__main__":
    main()
