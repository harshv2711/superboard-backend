import shutil
import tempfile
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Brand, Client, ClientOwner, NegativeRemark, NegativeRemarkOnTask, ScopeOfWork, ServiceCategory, Task, TypeOfWork
from .utils.task_points import calculate_designer_points, calculate_task_points

User = get_user_model()
TEST_MEDIA_ROOT = tempfile.mkdtemp()


class AuthProfileAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="profile@test.com",
            password="password123",
            role=User.Role.ART_DIRECTOR,
            first_name="Adi",
            last_name="Tyagi",
        )
        self.client.force_authenticate(self.user)

    def test_me_returns_profile_fields(self):
        response = self.client.get(reverse("auth-me"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "profile@test.com")
        self.assertEqual(response.data["first_name"], "Adi")
        self.assertEqual(response.data["last_name"], "Tyagi")
        self.assertEqual(response.data["role"], User.Role.ART_DIRECTOR)

    def test_user_can_update_own_profile(self):
        response = self.client.patch(
            reverse("auth-me"),
            {
                "first_name": "Aditya",
                "last_name": "Sharma",
                "email": "aditya@test.com",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Aditya")
        self.assertEqual(self.user.last_name, "Sharma")
        self.assertEqual(self.user.email, "aditya@test.com")

    def test_user_can_change_password(self):
        response = self.client.post(
            reverse("auth-change-password"),
            {
                "current_password": "password123",
                "new_password": "NewPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPassword123!"))

    def test_change_password_requires_correct_current_password(self):
        response = self.client.post(
            reverse("auth-change-password"),
            {
                "current_password": "wrong-password",
                "new_password": "NewPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("current_password", response.data)


class BrandAPITests(APITestCase):
    def setUp(self):
        self.brand_a = Brand.objects.create(name="Acme")
        self.brand_b = Brand.objects.create(name="Beta")
        self.list_url = reverse("brand-list")

    def test_list_brands(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_retrieve_brand(self):
        url = reverse("brand-detail", args=[self.brand_a.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Acme")

    def test_create_brand(self):
        response = self.client.post(self.list_url, {"name": "Gamma"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Gamma")

    def test_prevent_duplicate_brand_name_case_insensitive(self):
        response = self.client.post(self.list_url, {"name": "acme"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_update_brand(self):
        url = reverse("brand-detail", args=[self.brand_a.id])
        response = self.client.put(url, {"name": "Acme Updated"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.brand_a.refresh_from_db()
        self.assertEqual(self.brand_a.name, "Acme Updated")

    def test_partial_update_brand(self):
        url = reverse("brand-detail", args=[self.brand_a.id])
        response = self.client.patch(url, {"name": "Acme Patch"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.brand_a.refresh_from_db()
        self.assertEqual(self.brand_a.name, "Acme Patch")

    def test_delete_brand(self):
        url = reverse("brand-detail", args=[self.brand_b.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Brand.objects.filter(pk=self.brand_b.pk).exists())

    def test_search_brands_by_name(self):
        response = self.client.get(self.list_url, {"search": "acm"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item["name"] for item in response.data["results"]]
        self.assertEqual(names, ["Acme"])

    def test_order_brands_by_name_desc(self):
        response = self.client.get(self.list_url, {"ordering": "-name"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item["name"] for item in response.data["results"]]
        self.assertEqual(names, ["Beta", "Acme"])


class TypeOfWorkAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@test.com",
            password="password123",
            role=User.Role.ADMIN,
        )
        self.client.force_authenticate(self.user)
        self.category = ServiceCategory.objects.create(name="Digital Marketing", description="Marketing work")
        self.item_a = TypeOfWork.objects.create(
            service_category=self.category,
            work_type_name="Website Design",
            point=5.5,
        )
        self.item_b = TypeOfWork.objects.create(
            service_category=self.category,
            work_type_name="SEO Audit",
            point=3.25,
        )
        self.list_url = reverse("type-of-work-list")

    def test_list_type_of_work(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_retrieve_type_of_work(self):
        response = self.client.get(reverse("type-of-work-detail", args=[self.item_a.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["work_type_name"], "Website Design")
        self.assertEqual(response.data["service_category"], self.category.id)
        self.assertEqual(response.data["service_category_name"], "Digital Marketing")
        self.assertEqual(response.data["point"], 5.5)

    def test_create_type_of_work(self):
        response = self.client.post(
            self.list_url,
            {
                "service_category": self.category.id,
                "work_type_name": "Content Writing",
                "point": 2.75,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["service_category"], self.category.id)
        self.assertEqual(response.data["work_type_name"], "Content Writing")
        self.assertEqual(response.data["point"], 2.75)

    def test_prevent_duplicate_type_of_work_name_case_insensitive(self):
        response = self.client.post(
            self.list_url,
            {"work_type_name": "website design", "point": 7.5},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("work_type_name", response.data)

    def test_update_type_of_work(self):
        response = self.client.patch(
            reverse("type-of-work-detail", args=[self.item_a.id]),
            {
                "service_category": self.category.id,
                "work_type_name": "Website UI Design",
                "point": 6.75,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item_a.refresh_from_db()
        self.assertEqual(self.item_a.work_type_name, "Website UI Design")
        self.assertEqual(self.item_a.point, 6.75)

    def test_create_type_of_work_with_negative_float_point(self):
        response = self.client.post(
            self.list_url,
            {
                "service_category": self.category.id,
                "work_type_name": "Penalty Adjustment",
                "point": -2.5,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["point"], -2.5)


class NegativeRemarkAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="negative@test.com",
            password="password123",
            role=User.Role.ADMIN,
        )
        self.client.force_authenticate(self.user)
        self.client_obj = Client.objects.create(
            name="Pivot",
            client_interface="Harsh",
        )
        self.task = Task.objects.create(
            client=self.client_obj,
            task_name="Website Development",
            priority=Task.Priority.MEDIUM,
        )
        self.list_url = reverse("negative-remark-list")

    def test_create_negative_remark_supports_negative_float_point(self):
        response = self.client.post(
            self.list_url,
            {
                "remark_name": "Delay penalty",
                "description": "Missed expected turnaround",
                "point": -3.25,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["remark_name"], "Delay penalty")
        self.assertEqual(response.data["description"], "Missed expected turnaround")
        self.assertEqual(response.data["point"], "-3.2500")

    def test_list_negative_remarks(self):
        NegativeRemark.objects.create(
            remark_name="Penalty 1",
            description="Late submission",
            point=-2,
        )
        NegativeRemark.objects.create(
            remark_name="Penalty 2",
            description="Rework requested",
            point=-1.5,
        )

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)


class NegativeRemarkOnTaskAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="negative-link@test.com",
            password="password123",
            role=User.Role.ADMIN,
        )
        self.client.force_authenticate(self.user)
        self.client_obj = Client.objects.create(
            name="Pivot",
            client_interface="Harsh",
        )
        self.task = Task.objects.create(
            client=self.client_obj,
            task_name="Website Development",
            priority=Task.Priority.MEDIUM,
        )
        self.negative_remark = NegativeRemark.objects.create(
            remark_name="Delay penalty",
            description="Missed expected turnaround",
            point=-3.25,
        )
        self.list_url = reverse("negative-remark-on-task-list")

    def test_create_negative_remark_on_task(self):
        response = self.client.post(
            self.list_url,
            {
                "task": self.task.id,
                "negative_remark": self.negative_remark.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["task"], self.task.id)
        self.assertEqual(response.data["task_name"], "Website Development")
        self.assertEqual(response.data["negative_remark"], self.negative_remark.id)
        self.assertEqual(response.data["negative_remark_name"], "Delay penalty")
        self.assertEqual(response.data["negative_remark_description"], "Missed expected turnaround")
        self.assertEqual(response.data["point"], "-3.2500")

    def test_list_negative_remarks_on_task(self):
        NegativeRemarkOnTask.objects.create(task=self.task, negative_remark=self.negative_remark)

        response = self.client.get(self.list_url, {"task": self.task.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)


class TypeOfWorkQueryAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admin-query@test.com",
            password="password123",
            role=User.Role.ADMIN,
        )
        self.client.force_authenticate(self.user)
        self.category = ServiceCategory.objects.create(name="Digital Marketing", description="Marketing work")
        self.item_a = TypeOfWork.objects.create(
            service_category=self.category,
            work_type_name="Website Design",
            point=5.5,
        )
        self.item_b = TypeOfWork.objects.create(
            service_category=self.category,
            work_type_name="SEO Audit",
            point=3.25,
        )
        self.list_url = reverse("type-of-work-list")

    def test_delete_type_of_work(self):
        response = self.client.delete(reverse("type-of-work-detail", args=[self.item_b.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TypeOfWork.objects.filter(pk=self.item_b.pk).exists())

    def test_search_type_of_work_by_name(self):
        response = self.client.get(self.list_url, {"search": "seo"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item["work_type_name"] for item in response.data["results"]]
        self.assertEqual(names, ["SEO Audit"])

    def test_order_type_of_work_by_point_desc(self):
        response = self.client.get(self.list_url, {"ordering": "-point"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item["work_type_name"] for item in response.data["results"]]
        self.assertEqual(names, ["Website Design", "SEO Audit"])

    def test_filter_type_of_work_by_service_category(self):
        other_category = ServiceCategory.objects.create(name="Creative", description="Creative work")
        TypeOfWork.objects.create(service_category=other_category, work_type_name="Logo Design", point=9)

        response = self.client.get(self.list_url, {"service_category": self.category.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item["work_type_name"] for item in response.data["results"]]
        self.assertEqual(names, ["SEO Audit", "Website Design"])


class ServiceCategoryAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@test.com",
            password="password123",
            role=User.Role.ADMIN,
        )
        self.client.force_authenticate(self.user)
        self.category = ServiceCategory.objects.create(
            name="Digital Marketing",
            description="Digital campaigns and media",
        )
        self.type_of_work = TypeOfWork.objects.create(
            service_category=self.category,
            work_type_name="SEO Audit",
            point=3.25,
        )
        self.list_url = reverse("service-category-list")

    def test_list_service_categories(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Digital Marketing")

    def test_retrieve_service_category_includes_types_of_work(self):
        response = self.client.get(reverse("service-category-detail", args=[self.category.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Digital Marketing")
        self.assertEqual(len(response.data["types_of_work"]), 1)
        self.assertEqual(response.data["types_of_work"][0]["work_type_name"], "SEO Audit")

    def test_create_service_category(self):
        response = self.client.post(
            self.list_url,
            {"name": "Website Development", "description": "Build and maintain websites"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Website Development")

    def test_prevent_duplicate_service_category_name_case_insensitive(self):
        response = self.client.post(
            self.list_url,
            {"name": "digital marketing", "description": "Duplicate"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ClientAPITests(APITestCase):
    def setUp(self):
        self.planner = User.objects.create_user(
            email="planner@test.com",
            password="password123",
            role=User.Role.ACCOUNT_PLANNER,
        )
        self.client.force_authenticate(self.planner)
        self.client_obj = Client.objects.create(
            name="Acme Holdings",
            client_interface="harsh@acme.com",
            client_interface_contact_number="+91-9876543210",
            accent_color="#123456",
        )
        ClientOwner.objects.create(user=self.planner, client=self.client_obj)
        self.list_url = reverse("client-list")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def test_list_clients(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Acme Holdings")

    def test_create_client(self):
        payload = {
            "name": "Beta Ventures",
            "clientInterface": "anita@beta.com",
            "clientInterfaceContactNumber": "+91-9988776655",
            "accentColor": "#FF6600",
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Beta Ventures")
        self.assertEqual(response.data["clientInterfaceContactNumber"], "+91-9988776655")
        self.assertEqual(response.data["accentColor"], "#FF6600")
        self.assertTrue(ClientOwner.objects.filter(user=self.planner, client_id=response.data["id"]).exists())

    def test_create_client_with_logo(self):
        logo = SimpleUploadedFile(
            "logo.gif",
            (
                b"GIF87a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00"
                b"\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00"
                b"\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
            ),
            content_type="image/gif",
        )
        response = self.client.post(
            self.list_url,
            {
                "name": "Logo Client",
                "clientInterface": "logo@client.com",
                "clientInterfaceContactNumber": "",
                "logo": logo,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["logo"])

    def test_retrieve_client(self):
        response = self.client.get(reverse("client-detail", args=[self.client_obj.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["clientInterface"], "harsh@acme.com")
        self.assertEqual(response.data["clientInterfaceContactNumber"], "+91-9876543210")
        self.assertEqual(response.data["accentColor"], "#123456")

    def test_filter_clients_by_owner(self):
        other_planner = User.objects.create_user(
            email="planner2@test.com",
            password="password123",
            role=User.Role.ACCOUNT_PLANNER,
        )
        other_client = Client.objects.create(
            name="Beta Ventures",
            client_interface="anita@beta.com",
            client_interface_contact_number="+91-9988776655",
        )
        ClientOwner.objects.create(user=other_planner, client=other_client)

        response = self.client.get(self.list_url, {"owner": self.planner.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.client_obj.id)

    def test_non_owner_cannot_update_client(self):
        other_planner = User.objects.create_user(
            email="other@test.com",
            password="password123",
            role=User.Role.ACCOUNT_PLANNER,
        )
        self.client.force_authenticate(other_planner)

        response = self.client.patch(reverse("client-detail", args=[self.client_obj.id]), {"name": "Blocked"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_designer_cannot_create_client(self):
        designer = User.objects.create_user(
            email="designer@test.com",
            password="password123",
            role=User.Role.DESIGNER,
        )
        self.client.force_authenticate(designer)

        response = self.client.post(
            self.list_url,
            {"name": "Gamma", "clientInterface": "team@gamma.com", "clientInterfaceContactNumber": ""},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_art_director_cannot_create_client(self):
        art_director = User.objects.create_user(
            email="art@test.com",
            password="password123",
            role=User.Role.ART_DIRECTOR,
        )
        self.client.force_authenticate(art_director)

        response = self.client.post(
            self.list_url,
            {"name": "Gamma", "clientInterface": "team@gamma.com", "clientInterfaceContactNumber": ""},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ClientOwnerAPITests(APITestCase):
    def setUp(self):
        self.planner = User.objects.create_user(
            email="planner@test.com",
            password="password123",
            role=User.Role.ACCOUNT_PLANNER,
        )
        self.client.force_authenticate(self.planner)
        self.client_obj = Client.objects.create(
            name="Acme Holdings",
            client_interface="harsh@acme.com",
            client_interface_contact_number="+91-9876543210",
        )
        self.list_url = reverse("client-owner-list")

    def test_create_client_owner_mapping(self):
        payload = {"user": self.planner.id, "client": self.client_obj.id}

        response = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"], self.planner.id)
        self.assertEqual(response.data["client"], self.client_obj.id)
        self.assertTrue(ClientOwner.objects.filter(user=self.planner, client=self.client_obj).exists())

    def test_prevent_self_assign_to_owned_client(self):
        other_planner = User.objects.create_user(
            email="planner2@test.com",
            password="password123",
            role=User.Role.ACCOUNT_PLANNER,
        )
        ClientOwner.objects.create(user=other_planner, client=self.client_obj)

        response = self.client.post(self.list_url, {"user": self.planner.id, "client": self.client_obj.id}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_prevent_non_account_planner_assignment(self):
        designer = User.objects.create_user(
            email="designer@test.com",
            password="password123",
            role=User.Role.DESIGNER,
        )
        payload = {"user": designer.id, "client": self.client_obj.id}

        response = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("user", response.data)


class ScopeOfWorkAPITests(APITestCase):
    def setUp(self):
        self.planner = User.objects.create_user(
            email="planner@test.com",
            password="password123",
            role=User.Role.ACCOUNT_PLANNER,
        )
        self.client.force_authenticate(self.planner)
        self.client_obj = Client.objects.create(
            name="Acme Holdings",
            client_interface="harsh@acme.com",
            client_interface_contact_number="+91-9876543210",
        )
        ClientOwner.objects.create(user=self.planner, client=self.client_obj)
        self.category = ServiceCategory.objects.create(
            name="Social Media Management",
            description="Social media work",
        )
        self.type_of_work = TypeOfWork.objects.create(
            service_category=self.category,
            work_type_name="Social Post Design",
            point=2,
        )
        self.item = ScopeOfWork.objects.create(
            client=self.client_obj,
            service_category=self.category,
            deliverable_name="Content Calendar",
            description="Plan monthly social media posts",
            total_unit=1,
        )
        self.list_url = reverse("scope-of-work-list")

    def test_list_scope_of_work(self):
        self.item.type_of_work.set([self.type_of_work])
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["service_category"], self.category.id)
        self.assertEqual(response.data["results"][0]["service_category_name"], "Social Media Management")
        self.assertEqual(response.data["results"][0]["type_of_work"], [self.type_of_work.id])
        self.assertEqual(response.data["results"][0]["type_of_work_names"], [self.type_of_work.work_type_name])
        self.assertEqual(response.data["results"][0]["deliverable_name"], "Content Calendar")
        self.assertEqual(response.data["results"][0]["total_unit"], 1)
        self.assertEqual(response.data["results"][0]["client"], self.client_obj.id)

    def test_create_scope_of_work(self):
        performance_category = ServiceCategory.objects.create(name="Performance Marketing", description="Performance")
        ad_copy = TypeOfWork.objects.create(
            service_category=performance_category,
            work_type_name="Ad Copy",
            point=2,
        )
        campaign_design = TypeOfWork.objects.create(
            service_category=performance_category,
            work_type_name="Campaign Design",
            point=4,
        )
        payload = {
            "client": self.client_obj.id,
            "service_category": performance_category.id,
            "type_of_work": [ad_copy.id, campaign_design.id],
            "deliverable_name": "Campaign Setup",
            "description": "Setup paid campaigns",
            "total_unit": 2,
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["service_category"], performance_category.id)
        self.assertEqual(response.data["type_of_work"], [ad_copy.id, campaign_design.id])
        self.assertEqual(response.data["type_of_work_names"], ["Ad Copy", "Campaign Design"])
        self.assertEqual(response.data["deliverable_name"], "Campaign Setup")
        self.assertEqual(response.data["total_unit"], 2)

    def test_create_scope_of_work_rejects_type_of_work_from_other_service_category(self):
        other_category = ServiceCategory.objects.create(name="SEO", description="SEO work")
        wrong_type = TypeOfWork.objects.create(
            service_category=other_category,
            work_type_name="Audit",
            point=3,
        )

        response = self.client.post(
            self.list_url,
            {
                "client": self.client_obj.id,
                "service_category": self.category.id,
                "type_of_work": [wrong_type.id],
                "deliverable_name": "Content Calendar",
                "description": "Plan monthly social media posts",
                "total_unit": 1,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("type_of_work", response.data)

    def test_filter_scope_of_work_by_client(self):
        other_client = Client.objects.create(
            name="Beta Ventures",
            client_interface="anita@beta.com",
            client_interface_contact_number="+91-9988776655",
        )
        other_category = ServiceCategory.objects.create(name="Brand Guide", description="Brand guide work")
        ScopeOfWork.objects.create(
            client=other_client,
            service_category=other_category,
            deliverable_name="Strategy Meeting",
            description="Monthly strategy discussion",
            total_unit=1,
        )
        response = self.client.get(self.list_url, {"client": self.client_obj.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["client"], self.client_obj.id)

    def test_non_owner_cannot_create_scope_of_work(self):
        other_planner = User.objects.create_user(
            email="planner2@test.com",
            password="password123",
            role=User.Role.ACCOUNT_PLANNER,
        )
        self.client.force_authenticate(other_planner)

        response = self.client.post(
            self.list_url,
            {
                "client": self.client_obj.id,
                "service_category": ServiceCategory.objects.create(name="SEO", description="SEO work").id,
                "deliverable_name": "Audit",
                "description": "Review",
                "total_unit": 1,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_scope_of_work_with_optional_deliverable_and_description(self):
        response = self.client.post(
            self.list_url,
            {
                "client": self.client_obj.id,
                "service_category": ServiceCategory.objects.create(name="Custom Category", description="Custom").id,
                "deliverable_name": "",
                "description": "",
                "total_unit": 4,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["deliverable_name"], "")
        self.assertEqual(response.data["description"], "")
        self.assertEqual(response.data["total_unit"], 4)


class TaskAPITests(APITestCase):
    def setUp(self):
        self.client_obj = Client.objects.create(
            name="Acme Holdings",
            client_interface="harsh@acme.com",
            client_interface_contact_number="+91-9876543210",
        )
        self.planner = User.objects.create_user(
            email="planner@test.com",
            password="password123",
            role=User.Role.ACCOUNT_PLANNER,
        )
        self.client.force_authenticate(self.planner)
        ClientOwner.objects.create(user=self.planner, client=self.client_obj)
        self.designer = User.objects.create_user(
            email="designer@test.com",
            password="password123",
            role=User.Role.DESIGNER,
        )
        self.service_category = ServiceCategory.objects.create(
            name="Website Development",
            description="Website work",
        )
        self.type_of_work = TypeOfWork.objects.create(
            work_type_name="Website Design",
            point=5,
        )
        self.scope_of_work = ScopeOfWork.objects.create(
            client=self.client_obj,
            service_category=self.service_category,
            deliverable_name="Landing Page",
        )
        self.list_url = reverse("task-list")

    def test_create_task_with_target_date(self):
        payload = {
            "client": self.client_obj.id,
            "task_name": "Spring Campaign",
            "instructions": "Create launch assets",
            "scope_of_work": self.scope_of_work.id,
            "priority": Task.Priority.HIGH,
            "stage": Task.Stage.ON_GOING,
            "designer": self.designer.id,
            "type_of_work": self.type_of_work.id,
            "target_date": "2026-03-12",
            "impressions": 45000,
            "ctr": "3.25",
            "engagement_rate": "5.75",
            "promotion_type": Task.PromotionType.SPONSORED,
            "is_marked_completed_by_superadmin": True,
            "is_marked_completed_by_account_planner": True,
            "is_marked_completed_by_art_director": False,
            "is_marked_completed_by_designer": True,
            "excellence": "-3.25",
        }

        response = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["target_date"], "2026-03-12")
        self.assertEqual(response.data["priority"], Task.Priority.HIGH)
        self.assertEqual(response.data["stage"], Task.Stage.APPROVED)
        self.assertEqual(response.data["impressions"], 45000)
        self.assertEqual(response.data["ctr"], "3.25")
        self.assertEqual(response.data["engagement_rate"], "5.75")
        self.assertEqual(response.data["promotion_type"], Task.PromotionType.SPONSORED)
        self.assertEqual(response.data["type_of_work"], self.type_of_work.id)
        self.assertEqual(response.data["type_of_work_name"], "Website Design")
        self.assertEqual(response.data["service_category_name"], "Website Development")
        self.assertTrue(response.data["is_marked_completed_by_superadmin"])
        self.assertTrue(response.data["is_marked_completed_by_account_planner"])
        self.assertTrue(response.data["is_marked_completed_by_art_director"])
        self.assertTrue(response.data["is_marked_completed_by_designer"])
        self.assertFalse(response.data["isRevision"])
        self.assertEqual(response.data["excellence"], "-3.2500")
        self.assertEqual(Task.objects.get(pk=response.data["id"]).target_date.isoformat(), "2026-03-12")
        self.assertEqual(Task.objects.get(pk=response.data["id"]).promotion_type, Task.PromotionType.SPONSORED)

    def test_task_defaults_stage_to_backlog(self):
        response = self.client.post(
            self.list_url,
                {
                    "client": self.client_obj.id,
                    "task_name": "Default Stage Task",
                    "scope_of_work": self.scope_of_work.id,
                    "priority": Task.Priority.MEDIUM,
                },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["stage"], Task.Stage.BACKLOG)
        self.assertEqual(response.data["promotion_type"], Task.PromotionType.ORGANIC)

    def test_can_patch_task_stage_only(self):
        task = Task.objects.create(
            client=self.client_obj,
            scope_of_work=self.scope_of_work,
            task_name="Kanban Task",
            priority=Task.Priority.MEDIUM,
            stage=Task.Stage.BACKLOG,
        )

        response = self.client.patch(
            reverse("task-detail", args=[task.id]),
            {
                "stage": Task.Stage.APPROVED,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["stage"], Task.Stage.APPROVED)
        self.assertTrue(response.data["is_marked_completed_by_account_planner"])
        self.assertTrue(response.data["is_marked_completed_by_art_director"])
        self.assertTrue(response.data["is_marked_completed_by_designer"])
        task.refresh_from_db()
        self.assertEqual(task.stage, Task.Stage.APPROVED)
        derived_state = Task.completion_state_for_stage(task.stage)
        self.assertTrue(derived_state["is_marked_completed_by_account_planner"])
        self.assertTrue(derived_state["is_marked_completed_by_art_director"])
        self.assertTrue(derived_state["is_marked_completed_by_designer"])

    def test_designer_completion_flag_updates_stage(self):
        task = Task.objects.create(
            client=self.client_obj,
            scope_of_work=self.scope_of_work,
            task_name="Designer Complete Task",
            priority=Task.Priority.MEDIUM,
            stage=Task.Stage.ON_GOING,
        )

        response = self.client.patch(
            reverse("task-detail", args=[task.id]),
            {
                "is_marked_completed_by_designer": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["stage"], Task.Stage.COMPLETE)
        self.assertTrue(response.data["is_marked_completed_by_designer"])
        self.assertFalse(response.data["is_marked_completed_by_art_director"])
        self.assertFalse(response.data["is_marked_completed_by_account_planner"])
        task.refresh_from_db()
        self.assertEqual(task.stage, Task.Stage.COMPLETE)
        derived_state = Task.completion_state_for_stage(task.stage)
        self.assertTrue(derived_state["is_marked_completed_by_designer"])
        self.assertFalse(derived_state["is_marked_completed_by_art_director"])
        self.assertFalse(derived_state["is_marked_completed_by_account_planner"])

    def test_complete_stage_resets_higher_completion_flags(self):
        task = Task.objects.create(
            client=self.client_obj,
            scope_of_work=self.scope_of_work,
            task_name="Rollback Completion Task",
            priority=Task.Priority.MEDIUM,
            stage=Task.Stage.APPROVED,
        )

        response = self.client.patch(
            reverse("task-detail", args=[task.id]),
            {
                "stage": Task.Stage.COMPLETE,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["stage"], Task.Stage.COMPLETE)
        self.assertTrue(response.data["is_marked_completed_by_designer"])
        self.assertFalse(response.data["is_marked_completed_by_art_director"])
        self.assertFalse(response.data["is_marked_completed_by_account_planner"])

    def test_designer_kpi_endpoint_returns_monthly_total_for_designer(self):
        self.type_of_work.point = 2
        self.type_of_work.redo_point = 3
        self.type_of_work.major_changes_point = 1.5
        self.type_of_work.minor_changes_point = 0.5
        self.type_of_work.save()

        original = Task.objects.create(
            client=self.client_obj,
            scope_of_work=self.scope_of_work,
            task_name="Original Task",
            designer=self.designer,
            type_of_work=self.type_of_work,
            target_date="2026-03-15",
            slides=4,
            stage=Task.Stage.COMPLETE,
            excellence=Decimal("1.00"),
        )
        revision = Task.objects.create(
            revision_of=original,
            designer=self.designer,
            type_of_work=self.type_of_work,
            target_date="2026-03-18",
            slides=6,
            stage=Task.Stage.APPROVED_BY_ART_DIRECTOR_WAITING_FOR_APPROVAL,
            have_major_changes=True,
            excellence=Decimal("0.25"),
        )
        redo = Task.objects.create(
            redo_of=original,
            designer=self.designer,
            type_of_work=self.type_of_work,
            target_date="2026-03-22",
            slides=5,
            stage=Task.Stage.APPROVED,
            excellence=Decimal("0.75"),
        )
        Task.objects.create(
            client=self.client_obj,
            scope_of_work=self.scope_of_work,
            task_name="Second Task",
            designer=self.designer,
            type_of_work=self.type_of_work,
            target_date="2026-03-20",
            slides=2,
            stage=Task.Stage.COMPLETE,
        )
        Task.objects.create(
            client=self.client_obj,
            scope_of_work=self.scope_of_work,
            task_name="April Task",
            designer=self.designer,
            type_of_work=self.type_of_work,
            target_date="2026-04-02",
            slides=9,
            stage=Task.Stage.APPROVED,
        )
        Task.objects.create(
            client=self.client_obj,
            scope_of_work=self.scope_of_work,
            task_name="Backlog Task",
            designer=self.designer,
            type_of_work=self.type_of_work,
            target_date="2026-03-24",
            slides=7,
            stage=Task.Stage.BACKLOG,
        )

        low_quality = NegativeRemark.objects.create(remark_name="Low quality", point=Decimal("0.50"))
        missed_brief = NegativeRemark.objects.create(remark_name="Missed brief", point=Decimal("1.00"))
        typo = NegativeRemark.objects.create(remark_name="Typo", point=Decimal("0.25"))
        NegativeRemarkOnTask.objects.create(task=original, negative_remark=low_quality)
        NegativeRemarkOnTask.objects.create(task=revision, negative_remark=missed_brief)
        NegativeRemarkOnTask.objects.create(task=redo, negative_remark=typo)

        response = self.client.get(
            reverse("task-designer-kpi"),
            {"designer_id": self.designer.id, "month": "2026-03"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["designer_id"], self.designer.id)
        self.assertEqual(response.data["month"], "2026-03")
        self.assertAlmostEqual(response.data["total_kpi_score"], 20.75)

    def test_designer_kpi_endpoint_allows_designer_to_query_self_without_designer_id(self):
        self.client.force_authenticate(self.designer)
        Task.objects.create(
            client=self.client_obj,
            scope_of_work=self.scope_of_work,
            task_name="Self KPI Task",
            designer=self.designer,
            type_of_work=self.type_of_work,
            target_date="2026-03-10",
            slides=3,
            stage=Task.Stage.COMPLETE,
        )

        response = self.client.get(
            reverse("task-designer-kpi"),
            {"month": "2026-03"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["designer_id"], self.designer.id)
        self.assertEqual(response.data["month"], "2026-03")
        self.assertAlmostEqual(response.data["total_kpi_score"], 15.0)

    def test_task_excellence_accepts_integers_and_floats_including_negative_values(self):
        cases = [
            (5, "5.0000"),
            (5.5, "5.5000"),
            (-3, "-3.0000"),
            (-3.25, "-3.2500"),
        ]

        for value, expected in cases:
            response = self.client.post(
                self.list_url,
                {
                    "client": self.client_obj.id,
                    "task_name": f"Task {value}",
                    "scope_of_work": self.scope_of_work.id,
                    "priority": Task.Priority.HIGH,
                    "excellence": value,
                },
                format="json",
            )

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data["excellence"], expected)

    def test_task_name_is_required_for_standalone_task(self):
        response = self.client.post(
            self.list_url,
            {
                "client": self.client_obj.id,
                "task_name": "   ",
                "instructions": "Create launch assets",
                "priority": Task.Priority.HIGH,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["task_name"], ["Task name is required."])

    def test_non_owner_cannot_create_task(self):
        other_planner = User.objects.create_user(
            email="planner2@test.com",
            password="password123",
            role=User.Role.ACCOUNT_PLANNER,
        )
        self.client.force_authenticate(other_planner)

        response = self.client.post(
            self.list_url,
            {
                "client": self.client_obj.id,
                "task_name": "Blocked Task",
                "instructions": "No access",
                "priority": Task.Priority.MEDIUM,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_art_director_can_create_task(self):
        art_director = User.objects.create_user(
            email="art@test.com",
            password="password123",
            role=User.Role.ART_DIRECTOR,
        )
        self.client.force_authenticate(art_director)

        response = self.client.post(
            self.list_url,
            {
                "client": self.client_obj.id,
                "task_name": "AD Task",
                "priority": Task.Priority.HIGH,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["created_by"], art_director.id)

    def test_art_director_can_edit_account_planner_created_task(self):
        art_director = User.objects.create_user(
            email="art-lock@test.com",
            password="password123",
            role=User.Role.ART_DIRECTOR,
        )
        task = Task.objects.create(
            client=self.client_obj,
            task_name="Restricted Task",
            instructions="Original brief",
            priority=Task.Priority.MEDIUM,
            stage=Task.Stage.APPROVED,
            created_by=self.planner,
        )
        self.client.force_authenticate(art_director)

        response = self.client.patch(
            reverse("task-detail", args=[task.id]),
            {
                "instructions": "Updated brief",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.instructions, "Updated brief")

    def test_art_director_can_edit_own_created_task_but_not_planner_completion_flag(self):
        art_director = User.objects.create_user(
            email="art-own@test.com",
            password="password123",
            role=User.Role.ART_DIRECTOR,
        )
        task = Task.objects.create(
            client=self.client_obj,
            task_name="Restricted Task",
            instructions="Original brief",
            priority=Task.Priority.MEDIUM,
            stage=Task.Stage.APPROVED,
            created_by=art_director,
        )
        self.client.force_authenticate(art_director)

        response = self.client.patch(
            reverse("task-detail", args=[task.id]),
            {
                "instructions": "Updated brief",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.instructions, "Updated brief")

        response = self.client.patch(
            reverse("task-detail", args=[task.id]),
            {
                "is_marked_completed_by_account_planner": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("is_marked_completed_by_account_planner", response.data)

    def test_art_director_can_move_task_forward_and_backward_within_scope(self):
        art_director = User.objects.create_user(
            email="art-stage@test.com",
            password="password123",
            role=User.Role.ART_DIRECTOR,
        )
        task = Task.objects.create(
            client=self.client_obj,
            task_name="Art Director Workflow Task",
            instructions="Original brief",
            priority=Task.Priority.MEDIUM,
            stage=Task.Stage.COMPLETE,
            created_by=self.planner,
        )
        self.client.force_authenticate(art_director)

        forward_response = self.client.patch(
            reverse("task-detail", args=[task.id]),
            {
                "stage": Task.Stage.APPROVED_BY_ART_DIRECTOR_WAITING_FOR_APPROVAL,
            },
            format="json",
        )

        self.assertEqual(forward_response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.stage, Task.Stage.APPROVED_BY_ART_DIRECTOR_WAITING_FOR_APPROVAL)
        derived_state = Task.completion_state_for_stage(task.stage)
        self.assertTrue(derived_state["is_marked_completed_by_designer"])
        self.assertTrue(derived_state["is_marked_completed_by_art_director"])

        backward_response = self.client.patch(
            reverse("task-detail", args=[task.id]),
            {
                "stage": Task.Stage.COMPLETE,
            },
            format="json",
        )

        self.assertEqual(backward_response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.stage, Task.Stage.COMPLETE)
        derived_state = Task.completion_state_for_stage(task.stage)
        self.assertTrue(derived_state["is_marked_completed_by_designer"])
        self.assertFalse(derived_state["is_marked_completed_by_art_director"])

    def test_create_redo_task(self):
        original = Task.objects.create(
            client=self.client_obj,
            task_name="Launch Visual",
            instructions="Create key visual",
            priority=Task.Priority.HIGH,
            designer=self.designer,
        )

        response = self.client.post(
            self.list_url,
            {
                "redo_of": original.id,
                "task_name": original.task_name,
                "instructions": "Needs redo",
                "priority": Task.Priority.HIGH,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["redo_of"], original.id)
        self.assertEqual(response.data["redo_no"], 1)
        self.assertEqual(response.data["redo_count"], 1)
        self.assertTrue(response.data["isRedo"])
        self.assertEqual(response.data["task_name"], "Redo 1: Launch Visual")
        original.refresh_from_db()
        self.assertEqual(original.redo_count, 1)

    def test_designer_can_update_own_completion_flag(self):
        task = Task.objects.create(
            client=self.client_obj,
            task_name="Assigned Task",
            instructions="Do work",
            priority=Task.Priority.MEDIUM,
            designer=self.designer,
        )
        self.client.force_authenticate(self.designer)

        response = self.client.patch(
            reverse("task-detail", args=[task.id]),
            {
                "is_marked_completed_by_designer": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.stage, Task.Stage.COMPLETE)

    def test_designer_can_move_task_backward_within_own_stages(self):
        task = Task.objects.create(
            client=self.client_obj,
            task_name="Designer Workflow Task",
            instructions="Do work",
            priority=Task.Priority.MEDIUM,
            designer=self.designer,
            stage=Task.Stage.COMPLETE,
        )
        self.client.force_authenticate(self.designer)

        response = self.client.patch(
            reverse("task-detail", args=[task.id]),
            {
                "stage": Task.Stage.ON_GOING,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.stage, Task.Stage.ON_GOING)
        self.assertFalse(Task.completion_state_for_stage(task.stage)["is_marked_completed_by_designer"])

    def test_designer_can_move_task_from_complete_back_to_backlog(self):
        task = Task.objects.create(
            client=self.client_obj,
            task_name="Designer Reset Workflow Task",
            instructions="Do work",
            priority=Task.Priority.MEDIUM,
            designer=self.designer,
            stage=Task.Stage.COMPLETE,
        )
        self.client.force_authenticate(self.designer)

        response = self.client.patch(
            reverse("task-detail", args=[task.id]),
            {
                "stage": Task.Stage.BACKLOG,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.stage, Task.Stage.BACKLOG)
        derived_state = Task.completion_state_for_stage(task.stage)
        self.assertFalse(derived_state["is_marked_completed_by_designer"])
        self.assertFalse(derived_state["is_marked_completed_by_art_director"])
        self.assertFalse(derived_state["is_marked_completed_by_account_planner"])

    def test_designer_can_move_task_from_backlog_to_ongoing(self):
        task = Task.objects.create(
            client=self.client_obj,
            task_name="Designer Forward Workflow Task",
            instructions="Do work",
            priority=Task.Priority.MEDIUM,
            designer=self.designer,
            stage=Task.Stage.BACKLOG,
        )
        self.client.force_authenticate(self.designer)

        response = self.client.patch(
            reverse("task-detail", args=[task.id]),
            {
                "stage": Task.Stage.ON_GOING,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.stage, Task.Stage.ON_GOING)
        derived_state = Task.completion_state_for_stage(task.stage)
        self.assertFalse(derived_state["is_marked_completed_by_designer"])
        self.assertFalse(derived_state["is_marked_completed_by_art_director"])
        self.assertFalse(derived_state["is_marked_completed_by_account_planner"])

    def test_designer_cannot_move_task_beyond_own_stage_scope(self):
        task = Task.objects.create(
            client=self.client_obj,
            task_name="Designer Restricted Workflow Task",
            instructions="Do work",
            priority=Task.Priority.MEDIUM,
            designer=self.designer,
            stage=Task.Stage.COMPLETE,
        )
        self.client.force_authenticate(self.designer)

        response = self.client.patch(
            reverse("task-detail", args=[task.id]),
            {
                "stage": Task.Stage.APPROVED_BY_ART_DIRECTOR_WAITING_FOR_APPROVAL,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("stage", response.data)

    def test_designer_cannot_skip_forward_from_backlog_to_complete(self):
        task = Task.objects.create(
            client=self.client_obj,
            task_name="Designer Forward Skip Task",
            instructions="Do work",
            priority=Task.Priority.MEDIUM,
            designer=self.designer,
            stage=Task.Stage.BACKLOG,
        )
        self.client.force_authenticate(self.designer)

        response = self.client.patch(
            reverse("task-detail", args=[task.id]),
            {
                "stage": Task.Stage.COMPLETE,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("stage", response.data)

    def test_account_planner_cannot_update_art_director_or_designer_completion_flags(self):
        task = Task.objects.create(
            client=self.client_obj,
            task_name="Planner Restricted Task",
            instructions="Check flags",
            priority=Task.Priority.MEDIUM,
            designer=self.designer,
        )

        response = self.client.patch(
            reverse("task-detail", args=[task.id]),
            {
                "is_marked_completed_by_art_director": True,
                "is_marked_completed_by_designer": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        task.refresh_from_db()
        derived_state = Task.completion_state_for_stage(task.stage)
        self.assertFalse(derived_state["is_marked_completed_by_art_director"])
        self.assertFalse(derived_state["is_marked_completed_by_designer"])

    def test_account_planner_can_still_update_own_completion_flag(self):
        task = Task.objects.create(
            client=self.client_obj,
            task_name="Planner Allowed Task",
            instructions="Own flag only",
            priority=Task.Priority.MEDIUM,
            designer=self.designer,
        )

        response = self.client.patch(
            reverse("task-detail", args=[task.id]),
            {
                "is_marked_completed_by_account_planner": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.stage, Task.Stage.APPROVED)

    def test_account_planner_can_move_task_forward_and_backward_within_scope(self):
        task = Task.objects.create(
            client=self.client_obj,
            scope_of_work=self.scope_of_work,
            task_name="Planner Workflow Task",
            priority=Task.Priority.MEDIUM,
            stage=Task.Stage.APPROVED_BY_ART_DIRECTOR_WAITING_FOR_APPROVAL,
        )

        forward_response = self.client.patch(
            reverse("task-detail", args=[task.id]),
            {
                "stage": Task.Stage.APPROVED,
            },
            format="json",
        )

        self.assertEqual(forward_response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.stage, Task.Stage.APPROVED)
        self.assertTrue(Task.completion_state_for_stage(task.stage)["is_marked_completed_by_account_planner"])

        backward_response = self.client.patch(
            reverse("task-detail", args=[task.id]),
            {
                "stage": Task.Stage.APPROVED_BY_ART_DIRECTOR_WAITING_FOR_APPROVAL,
            },
            format="json",
        )

        self.assertEqual(backward_response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.stage, Task.Stage.APPROVED_BY_ART_DIRECTOR_WAITING_FOR_APPROVAL)
        self.assertFalse(Task.completion_state_for_stage(task.stage)["is_marked_completed_by_account_planner"])

    def test_account_planner_cannot_skip_outside_own_scope(self):
        task = Task.objects.create(
            client=self.client_obj,
            scope_of_work=self.scope_of_work,
            task_name="Planner Restricted Workflow Task",
            priority=Task.Priority.MEDIUM,
            stage=Task.Stage.APPROVED_BY_ART_DIRECTOR_WAITING_FOR_APPROVAL,
        )

        response = self.client.patch(
            reverse("task-detail", args=[task.id]),
            {
                "stage": Task.Stage.COMPLETE,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("stage", response.data)

    def test_designer_cannot_update_other_task_fields(self):
        task = Task.objects.create(
            client=self.client_obj,
            task_name="Assigned Task",
            instructions="Do work",
            priority=Task.Priority.MEDIUM,
            designer=self.designer,
        )
        self.client.force_authenticate(self.designer)

        response = self.client.patch(
            reverse("task-detail", args=[task.id]),
            {
                "priority": Task.Priority.HIGH,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_designer_cannot_create_task(self):
        self.client.force_authenticate(self.designer)

        response = self.client.post(
            self.list_url,
            {
                "client": self.client_obj.id,
                "task_name": "Blocked",
                "instructions": "No create",
                "priority": Task.Priority.MEDIUM,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_designer_cannot_delete_task(self):
        task = Task.objects.create(
            client=self.client_obj,
            task_name="Assigned Task",
            instructions="Do work",
            priority=Task.Priority.MEDIUM,
            designer=self.designer,
        )
        self.client.force_authenticate(self.designer)

        response = self.client.delete(reverse("task-detail", args=[task.id]))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_designer_only_sees_own_tasks(self):
        other_designer = User.objects.create_user(
            email="designer2@test.com",
            password="password123",
            role=User.Role.DESIGNER,
        )
        own_task = Task.objects.create(
            client=self.client_obj,
            task_name="Own Task",
            instructions="Own work",
            priority=Task.Priority.MEDIUM,
            designer=self.designer,
        )
        Task.objects.create(
            client=self.client_obj,
            task_name="Other Task",
            instructions="Other work",
            priority=Task.Priority.MEDIUM,
            designer=other_designer,
        )
        self.client.force_authenticate(self.designer)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(returned_ids, [own_task.id])

    def test_revision_response_exposes_is_revision(self):
        original = Task.objects.create(
            client=self.client_obj,
            task_name="Original Task",
            instructions="Original",
            target_date="2026-03-12",
            designer=self.designer,
        )
        revision = Task.objects.create(
            revision_of=original,
            task_name="Original Task",
            instructions="Revision",
            priority=Task.Priority.LOW,
            target_date="2026-03-13",
            designer=self.designer,
        )

        response = self.client.get(reverse("task-detail", args=[revision.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["isRevision"])
        self.assertEqual(response.data["revision_of_task_name"], "Original Task")
        self.assertEqual(response.data["priority"], Task.Priority.LOW)

    def test_nested_revision_points_to_previous_revision_and_increments_revision_number(self):
        original = Task.objects.create(
            client=self.client_obj,
            task_name="Original Task",
            instructions="Original",
            target_date="2026-03-12",
            designer=self.designer,
        )
        revision_one = Task.objects.create(
            revision_of=original,
            task_name="Original Task",
            instructions="Revision 1",
            priority=Task.Priority.LOW,
            target_date="2026-03-13",
            designer=self.designer,
        )

        response = self.client.post(
            self.list_url,
            {
                "revision_of": revision_one.id,
                "task_name": revision_one.task_name,
                "instructions": "Revision 2",
                "priority": Task.Priority.LOW,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["revision_of"], revision_one.id)
        self.assertEqual(response.data["revision_no"], 2)
        self.assertEqual(response.data["task_name"], "Revision 2: Original Task")

    def test_redo_response_exposes_is_redo(self):
        original = Task.objects.create(
            client=self.client_obj,
            task_name="Original Task",
            instructions="Original",
            target_date="2026-03-12",
            designer=self.designer,
        )
        redo = Task.objects.create(
            redo_of=original,
            task_name="Original Task",
            instructions="Redo",
            priority=Task.Priority.LOW,
            target_date="2026-03-13",
            designer=self.designer,
        )

        response = self.client.get(reverse("task-detail", args=[redo.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["isRedo"])
        self.assertEqual(response.data["redo_of"], original.id)
        self.assertEqual(response.data["redo_of_task_name"], "Original Task")
        self.assertEqual(response.data["redo_of_task_id"], original.id)
        self.assertEqual(response.data["priority"], Task.Priority.LOW)

    def test_delete_task_with_linked_revision_returns_clear_message(self):
        original = Task.objects.create(
            client=self.client_obj,
            task_name="Original Task",
            instructions="Original",
            priority=Task.Priority.MEDIUM,
            designer=self.designer,
        )
        Task.objects.create(
            revision_of=original,
            task_name="Original Task",
            instructions="Revision",
            priority=Task.Priority.LOW,
            designer=self.designer,
        )

        response = self.client.delete(reverse("task-detail", args=[original.id]))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "Cannot delete the task because Original Task is associated with another task (revision).",
        )


class TaskPointsUtilsTests(TestCase):
    def setUp(self):
        self.designer = User.objects.create_user(email="designer@test.com", password="password123")
        self.other_designer = User.objects.create_user(email="other@test.com", password="password123")
        self.client_obj = Client.objects.create(name="Pivot", client_interface="Harsh")

    def test_calculate_task_points_matches_carousel_example(self):
        carousel = TypeOfWork.objects.create(
            work_type_name="Carousel Post",
            point=0.5,
            redo_point=1.0,
            major_changes_point=0.0,
            minor_changes_point=0.25,
        )
        original = Task.objects.create(
            client=self.client_obj,
            task_name="Carousel",
            designer=self.designer,
            type_of_work=carousel,
            slides=3,
        )
        Task.objects.create(
            revision_of=original,
            task_name="Carousel",
            designer=self.designer,
            type_of_work=carousel,
            slides=5,
            have_minor_changes=True,
        )
        redo = Task.objects.create(
            redo_of=original,
            task_name="Carousel",
            designer=self.designer,
            type_of_work=carousel,
            slides=2,
        )
        Task.objects.create(
            revision_of=redo,
            task_name="Carousel",
            designer=self.designer,
            type_of_work=carousel,
            slides=4,
            have_major_changes=True,
        )

        self.assertEqual(calculate_task_points(original), 6.75)

    def test_calculate_task_points_includes_negative_remarks_and_excellence(self):
        homepage = TypeOfWork.objects.create(
            work_type_name="Home Page & Product Page",
            point=4.0,
            redo_point=2.0,
            major_changes_point=1.0,
            minor_changes_point=0.0,
        )
        original = Task.objects.create(
            client=self.client_obj,
            task_name="Homepage",
            designer=self.designer,
            type_of_work=homepage,
            slides=1,
            excellence=Decimal("5.0"),
        )
        Task.objects.create(
            revision_of=original,
            task_name="Homepage",
            designer=self.designer,
            type_of_work=homepage,
            have_major_changes=True,
        )
        negative_remark = NegativeRemark.objects.create(
            remark_name="Missed detail",
            point=Decimal("-0.5"),
        )
        NegativeRemarkOnTask.objects.create(task=original, negative_remark=negative_remark)

        self.assertEqual(calculate_task_points(original), 9.5)

    def test_calculate_task_points_returns_zero_without_type_of_work(self):
        original = Task.objects.create(
            client=self.client_obj,
            task_name="Untyped Task",
            designer=self.designer,
        )

        self.assertEqual(calculate_task_points(original), 0.0)

    def test_calculate_task_points_rejects_revision_and_redo_tasks(self):
        static_post = TypeOfWork.objects.create(
            work_type_name="Static Post",
            point=1.0,
            redo_point=1.0,
            major_changes_point=0.5,
            minor_changes_point=0.25,
        )
        original = Task.objects.create(
            client=self.client_obj,
            task_name="Static Post",
            designer=self.designer,
            type_of_work=static_post,
        )
        revision = Task.objects.create(
            revision_of=original,
            task_name="Static Post",
            designer=self.designer,
            type_of_work=static_post,
            have_major_changes=True,
        )
        redo = Task.objects.create(
            redo_of=original,
            task_name="Static Post",
            designer=self.designer,
            type_of_work=static_post,
        )

        with self.assertRaises(ValueError):
            calculate_task_points(revision)

        with self.assertRaises(ValueError):
            calculate_task_points(redo)

    def test_calculate_designer_points_sums_only_original_tasks_for_designer(self):
        carousel = TypeOfWork.objects.create(
            work_type_name="Designer Carousel",
            point=0.5,
            redo_point=1.0,
            major_changes_point=0.0,
            minor_changes_point=0.25,
        )
        static_post = TypeOfWork.objects.create(
            work_type_name="Designer Static Post",
            point=1.0,
            redo_point=1.0,
            major_changes_point=0.5,
            minor_changes_point=0.25,
        )

        original_one = Task.objects.create(
            client=self.client_obj,
            task_name="Carousel",
            designer=self.designer,
            type_of_work=carousel,
            slides=3,
        )
        Task.objects.create(
            revision_of=original_one,
            task_name="Carousel",
            designer=self.designer,
            type_of_work=carousel,
            slides=5,
            have_minor_changes=True,
        )
        redo = Task.objects.create(
            redo_of=original_one,
            task_name="Carousel",
            designer=self.designer,
            type_of_work=carousel,
            slides=2,
        )
        Task.objects.create(
            revision_of=redo,
            task_name="Carousel",
            designer=self.designer,
            type_of_work=carousel,
            slides=4,
            have_major_changes=True,
        )

        Task.objects.create(
            client=self.client_obj,
            task_name="Static",
            designer=self.designer,
            type_of_work=static_post,
        )
        Task.objects.create(
            revision_of=original_one,
            task_name="Carousel",
            designer=self.designer,
            type_of_work=carousel,
            have_major_changes=True,
        )
        Task.objects.create(
            client=self.client_obj,
            task_name="No Type",
            designer=self.designer,
        )
        Task.objects.create(
            client=self.client_obj,
            task_name="Other Designer Task",
            designer=self.other_designer,
            type_of_work=static_post,
        )

        self.assertEqual(calculate_designer_points(self.designer), 7.75)
