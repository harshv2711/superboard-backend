from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from api.models import (
    Brand,
    Client,
    ClientAttachment,
    ClientMonthlyAmount,
    ClientOwner,
    Group,
    GroupMember,
    NegativeRemark,
    NegativeRemarkOnTask,
    ScopeOfWork,
    ServiceCategory,
    Task,
    TaskAttachment,
    TaskOnStage,
    TaskStage,
    TypeOfWork,
)
from users.models import Employee


class Command(BaseCommand):
    help = "Seed dummy data for the main Superboard models."

    def add_arguments(self, parser):
        parser.add_argument(
            "--bulk-tasks",
            type=int,
            default=0,
            help="Create additional standalone tasks for pagination and stress testing.",
        )

    def handle(self, *args, **options):
        bulk_tasks = max(0, options["bulk_tasks"])
        user_model = get_user_model()

        user_seed = [
            {
                "key": "super_admin",
                "email": "harsh@pivot.test",
                "first_name": "Harsh",
                "last_name": "Admin",
                "role": user_model.Role.SUPERUSER,
                "is_staff": True,
                "is_superuser": True,
                "designation": "Super Admin",
                "salary": None,
            },
            {
                "key": "ops_admin",
                "email": "ops@pivot.test",
                "first_name": "Ops",
                "last_name": "Admin",
                "role": user_model.Role.ADMIN,
                "is_staff": True,
                "is_superuser": False,
                "designation": "Operations Admin",
                "salary": None,
            },
            {
                "key": "rhea_planner",
                "email": "rhea@pivot.test",
                "first_name": "Rhea",
                "last_name": "Kapoor",
                "role": user_model.Role.ACCOUNT_PLANNER,
                "designation": "Account Planner",
                "salary": Decimal("55000.00"),
            },
            {
                "key": "arjun_planner",
                "email": "arjun@pivot.test",
                "first_name": "Arjun",
                "last_name": "Mehta",
                "role": user_model.Role.ACCOUNT_PLANNER,
                "designation": "Senior Account Planner",
                "salary": Decimal("62000.00"),
            },
            {
                "key": "aditya_art",
                "email": "aditya@pivot.test",
                "first_name": "Aditya",
                "last_name": "Verma",
                "role": user_model.Role.ART_DIRECTOR,
                "designation": "Art Director",
                "salary": Decimal("78000.00"),
            },
            {
                "key": "megha_art",
                "email": "megha@pivot.test",
                "first_name": "Megha",
                "last_name": "Sharma",
                "role": user_model.Role.ART_DIRECTOR,
                "designation": "Associate Art Director",
                "salary": Decimal("72000.00"),
            },
            {
                "key": "ava_designer",
                "email": "ava@pivot.test",
                "first_name": "Ava",
                "last_name": "Shaw",
                "role": user_model.Role.DESIGNER,
                "designation": "Graphic Designer",
                "salary": Decimal("40000.00"),
            },
            {
                "key": "liam_creative",
                "email": "liam@pivot.test",
                "first_name": "Liam",
                "last_name": "Cole",
                "role": user_model.Role.DESIGNER,
                "designation": "Motion Designer",
                "salary": Decimal("43000.00"),
            },
            {
                "key": "maya_visuals",
                "email": "maya@pivot.test",
                "first_name": "Maya",
                "last_name": "Rao",
                "role": user_model.Role.DESIGNER,
                "designation": "Visual Designer",
                "salary": Decimal("41000.00"),
            },
            {
                "key": "noah_motion",
                "email": "noah@pivot.test",
                "first_name": "Noah",
                "last_name": "Kerr",
                "role": user_model.Role.DESIGNER,
                "designation": "Senior Designer",
                "salary": Decimal("46000.00"),
            },
            {
                "key": "hr_anjali",
                "email": "anjali@pivot.test",
                "first_name": "Anjali",
                "last_name": "Nair",
                "role": user_model.Role.HUMAN_RESOURCE,
                "designation": "HR Manager",
                "salary": Decimal("50000.00"),
            },
        ]

        service_categories_seed = [
            ("Social Media Management", "Creative production for social posts, reels, and stories."),
            ("Performance Marketing", "Performance-first ad creatives for paid media."),
            ("Brand Collateral", "Sales, retail, and communication collateral."),
            ("Website Development", "Website visuals, UX assets, and landing page content."),
            ("Brand Guide", "Identity systems, guides, and governance assets."),
            ("Brand Logo", "Logo explorations and identity marks."),
            ("SEO", "Content visuals and supporting search-focused creative assets."),
        ]

        type_of_work_seed = [
            ("Ad Creative", Decimal("1.50"), Decimal("1.00"), Decimal("0.75"), Decimal("0.30")),
            ("Social Media Post", Decimal("1.00"), Decimal("0.80"), Decimal("0.50"), Decimal("0.25")),
            ("Website Banner", Decimal("1.75"), Decimal("1.20"), Decimal("0.80"), Decimal("0.35")),
            ("Brochure/ Brand book", Decimal("2.25"), Decimal("1.50"), Decimal("1.00"), Decimal("0.50")),
            ("Presentation", Decimal("2.00"), Decimal("1.25"), Decimal("0.90"), Decimal("0.40")),
            ("Packaging", Decimal("2.50"), Decimal("1.75"), Decimal("1.10"), Decimal("0.55")),
            ("Video Storyboard", Decimal("2.20"), Decimal("1.60"), Decimal("1.00"), Decimal("0.45")),
        ]

        negative_remarks_seed = [
            ("Missing Clients deadline (-2)", "Penalty when deliverables miss the client deadline.", Decimal("-2.00")),
            ("Post Hygiene (-0.5)", "Penalty for formatting or quality misses in final output.", Decimal("-0.50")),
            ("Brand Guideline Miss (-1)", "Penalty when the task drifts from brand standards.", Decimal("-1.00")),
            ("Wrong Size Export (-0.25)", "Penalty for incorrect export size or platform output.", Decimal("-0.25")),
        ]

        client_seed = [
            {
                "name": "Web Packaging Solution",
                "client_interface": "Ritika Sethi",
                "contact": "+91-9900011101",
                "accent_color": "#3B82F6",
                "monthly_amounts": [Decimal("185000.00"), Decimal("190000.00"), Decimal("195000.00")],
            },
            {
                "name": "Unifab",
                "client_interface": "Rohan Arora",
                "contact": "+91-9900011102",
                "accent_color": "#F97316",
                "monthly_amounts": [Decimal("145000.00"), Decimal("150000.00"), Decimal("152500.00")],
            },
            {
                "name": "James Douglas India",
                "client_interface": "Kabir Shah",
                "contact": "+91-9900011103",
                "accent_color": "#8B5CF6",
                "monthly_amounts": [Decimal("132000.00"), Decimal("134000.00"), Decimal("138000.00")],
            },
            {
                "name": "TVS Rubber",
                "client_interface": "Mitali Verma",
                "contact": "+91-9900011104",
                "accent_color": "#10B981",
                "monthly_amounts": [Decimal("98000.00"), Decimal("102000.00"), Decimal("108000.00")],
            },
            {
                "name": "Ema Partners",
                "client_interface": "Neha Kapoor",
                "contact": "+91-9900011105",
                "accent_color": "#EC4899",
                "monthly_amounts": [Decimal("125000.00"), Decimal("130000.00"), Decimal("133000.00")],
            },
        ]

        scope_seed = [
            {
                "client": "Web Packaging Solution",
                "service_category": "Brand Collateral",
                "deliverable_name": "Sales Brochure Program",
                "description": "Brochures, sales sheets, and packaging support collaterals.",
                "total_unit": 12,
                "type_of_work": ["Brochure/ Brand book", "Presentation", "Packaging"],
            },
            {
                "client": "Web Packaging Solution",
                "service_category": "Website Development",
                "deliverable_name": "Product Page Asset System",
                "description": "Hero visuals and supporting banners for the product site.",
                "total_unit": 8,
                "type_of_work": ["Website Banner", "Ad Creative"],
            },
            {
                "client": "Unifab",
                "service_category": "Social Media Management",
                "deliverable_name": "Monthly Social Calendar",
                "description": "Original posts, revisions, and campaign assets for monthly publishing.",
                "total_unit": 18,
                "type_of_work": ["Social Media Post", "Ad Creative", "Video Storyboard"],
            },
            {
                "client": "James Douglas India",
                "service_category": "Performance Marketing",
                "deliverable_name": "Lead Generation Creative Set",
                "description": "Static and motion campaign ads for paid acquisition.",
                "total_unit": 14,
                "type_of_work": ["Ad Creative", "Video Storyboard"],
            },
            {
                "client": "TVS Rubber",
                "service_category": "Brand Guide",
                "deliverable_name": "Trade Identity Toolkit",
                "description": "Trade and dealership brand support assets.",
                "total_unit": 6,
                "type_of_work": ["Presentation", "Brochure/ Brand book"],
            },
            {
                "client": "Ema Partners",
                "service_category": "Social Media Management",
                "deliverable_name": "Leadership Branding Pack",
                "description": "Thought-leadership posts and employer branding visuals.",
                "total_unit": 10,
                "type_of_work": ["Social Media Post", "Website Banner"],
            },
        ]

        task_seed = [
            {
                "client": "Web Packaging Solution",
                "scope": "Sales Brochure Program",
                "task_name": "WPS Intel Brochure",
                "instructions": "Create a refreshed Intel brochure with updated product positioning.",
                "art_instructions": "Keep the layout premium and brochure-led.",
                "type_of_work": "Brochure/ Brand book",
                "platform": "",
                "slides": 12,
                "priority": Task.Priority.HIGH,
                "promotion_type": Task.PromotionType.ORGANIC,
                "designer": "ava_designer",
                "created_by": "rhea_planner",
                "target_date": date(2026, 3, 30),
                "stage": Task.Stage.COMPLETE,
                "impressions": 1200,
                "ctr": Decimal("1.20"),
                "engagement_rate": Decimal("3.40"),
                "have_major_changes": False,
                "have_minor_changes": True,
                "excellence": Decimal("0.50"),
                "excellence_reason": "Strong refinement and polished brochure system.",
                "negative_remarks": ["Post Hygiene (-0.5)"],
                "revisions": [
                    {
                        "revision_no": 1,
                        "designer": "maya_visuals",
                        "target_date": date(2026, 3, 31),
                        "stage": Task.Stage.APPROVED,
                        "have_major_changes": False,
                        "have_minor_changes": True,
                        "revision_type": Task.RevisionType.MEDIUM,
                    }
                ],
                "redos": [
                    {
                        "redo_no": 1,
                        "designer": "liam_creative",
                        "target_date": date(2026, 4, 2),
                        "stage": Task.Stage.ON_GOING,
                    }
                ],
            },
            {
                "client": "Unifab",
                "scope": "Monthly Social Calendar",
                "task_name": "Instagram Static Post 1",
                "instructions": "Design the first static post for the Unifab March campaign.",
                "art_instructions": "Focus on clean product framing with campaign typography.",
                "type_of_work": "Ad Creative",
                "platform": Task.Platform.INSTAGRAM,
                "slides": 2,
                "priority": Task.Priority.HIGH,
                "promotion_type": Task.PromotionType.SPONSORED,
                "designer": "maya_visuals",
                "created_by": "arjun_planner",
                "target_date": date(2026, 3, 30),
                "stage": Task.Stage.APPROVED_BY_ART_DIRECTOR_WAITING_FOR_APPROVAL,
                "impressions": 2400,
                "ctr": Decimal("1.75"),
                "engagement_rate": Decimal("4.80"),
                "have_major_changes": True,
                "have_minor_changes": False,
                "excellence": Decimal("0.25"),
                "excellence_reason": "Strong visual hierarchy across variants.",
                "negative_remarks": ["Missing Clients deadline (-2)"],
                "revisions": [
                    {
                        "revision_no": 1,
                        "designer": "noah_motion",
                        "target_date": date(2026, 3, 31),
                        "stage": Task.Stage.COMPLETE,
                        "have_major_changes": False,
                        "have_minor_changes": True,
                        "revision_type": Task.RevisionType.SMALL,
                    }
                ],
                "redos": [],
            },
            {
                "client": "James Douglas India",
                "scope": "Lead Generation Creative Set",
                "task_name": "James Douglas Lead Ad Series",
                "instructions": "Create a lead generation ad set for India market outreach.",
                "art_instructions": "Prioritize clarity and conversion-first visual pacing.",
                "type_of_work": "Ad Creative",
                "platform": Task.Platform.LINKEDIN,
                "slides": 4,
                "priority": Task.Priority.MEDIUM,
                "promotion_type": Task.PromotionType.SPONSORED,
                "designer": "liam_creative",
                "created_by": "rhea_planner",
                "target_date": date(2026, 4, 3),
                "stage": Task.Stage.ON_GOING,
                "impressions": 1800,
                "ctr": Decimal("0.95"),
                "engagement_rate": Decimal("2.30"),
                "have_major_changes": False,
                "have_minor_changes": False,
                "excellence": None,
                "excellence_reason": "",
                "negative_remarks": [],
                "revisions": [],
                "redos": [],
            },
            {
                "client": "TVS Rubber",
                "scope": "Trade Identity Toolkit",
                "task_name": "Dealer Presentation Deck",
                "instructions": "Prepare a dealer communication presentation deck for trade outreach.",
                "art_instructions": "Keep it industrial, clear, and sales-oriented.",
                "type_of_work": "Presentation",
                "platform": "",
                "slides": 18,
                "priority": Task.Priority.LOW,
                "promotion_type": Task.PromotionType.ORGANIC,
                "designer": "noah_motion",
                "created_by": "arjun_planner",
                "target_date": date(2026, 2, 26),
                "stage": Task.Stage.APPROVED,
                "impressions": 950,
                "ctr": Decimal("0.60"),
                "engagement_rate": Decimal("1.80"),
                "have_major_changes": False,
                "have_minor_changes": True,
                "excellence": Decimal("0.15"),
                "excellence_reason": "Good content modularity.",
                "negative_remarks": ["Wrong Size Export (-0.25)"],
                "revisions": [],
                "redos": [],
            },
            {
                "client": "Ema Partners",
                "scope": "Leadership Branding Pack",
                "task_name": "Leadership LinkedIn Carousel",
                "instructions": "Design a LinkedIn carousel for leadership branding content.",
                "art_instructions": "Keep it executive and minimal.",
                "type_of_work": "Social Media Post",
                "platform": Task.Platform.LINKEDIN,
                "slides": 6,
                "priority": Task.Priority.MEDIUM,
                "promotion_type": Task.PromotionType.ORGANIC,
                "designer": "ava_designer",
                "created_by": "rhea_planner",
                "target_date": date(2026, 1, 18),
                "stage": Task.Stage.BACKLOG,
                "impressions": 0,
                "ctr": Decimal("0.00"),
                "engagement_rate": Decimal("0.00"),
                "have_major_changes": False,
                "have_minor_changes": False,
                "excellence": None,
                "excellence_reason": "",
                "negative_remarks": ["Brand Guideline Miss (-1)"],
                "revisions": [],
                "redos": [],
            },
        ]

        stage_mapping = {
            Task.Stage.BACKLOG: "Initiate",
            Task.Stage.ON_GOING: "Ongoing",
            Task.Stage.COMPLETE: "Complete",
            Task.Stage.APPROVED_BY_ART_DIRECTOR_WAITING_FOR_APPROVAL: "Approved By Art Director",
            Task.Stage.APPROVED: "Approved by Client",
        }

        stage_style_rank = {
            Task.Stage.BACKLOG: 0,
            Task.Stage.ON_GOING: 1,
            Task.Stage.COMPLETE: 2,
            Task.Stage.APPROVED_BY_ART_DIRECTOR_WAITING_FOR_APPROVAL: 3,
            Task.Stage.APPROVED: 4,
        }

        def sync_stage_link(task, stage_records):
            stage_record = stage_records[task.stage]
            TaskOnStage.objects.update_or_create(task=task, defaults={"task_stage": stage_record})

        def attach_file(field_file, name, content):
            if field_file:
                field_file.delete(save=False)
            field_file.save(name, ContentFile(content), save=True)

        self.stdout.write("Preparing seed data reset for API models.")
        TaskOnStage.objects.all().delete()
        NegativeRemarkOnTask.objects.all().delete()
        TaskAttachment.objects.all().delete()
        Task.objects.all().delete()
        ClientAttachment.objects.all().delete()
        ClientMonthlyAmount.objects.all().delete()
        ClientOwner.objects.all().delete()
        GroupMember.objects.all().delete()
        Group.objects.all().delete()
        ScopeOfWork.objects.all().delete()
        NegativeRemark.objects.all().delete()
        TaskStage.objects.all().delete()
        Client.objects.all().delete()
        Brand.objects.all().delete()
        ServiceCategory.objects.all().delete()
        TypeOfWork.objects.all().delete()

        users = {}
        for item in user_seed:
            defaults = {
                "first_name": item["first_name"],
                "last_name": item["last_name"],
                "role": item["role"],
                "is_staff": item.get("is_staff", False),
                "is_superuser": item.get("is_superuser", False),
                "is_active": True,
            }
            user, created = user_model.objects.update_or_create(email=item["email"], defaults=defaults)
            if not user.has_usable_password():
                user.set_password("pivot123")
                user.save(update_fields=["password"])
            users[item["key"]] = user
            self.stdout.write(f"{'Created' if created else 'Updated'} user: {user.email}")

            salary = item.get("salary")
            if salary is not None:
                Employee.objects.update_or_create(
                    user=user,
                    defaults={
                        "designation": item["designation"],
                        "salary": salary,
                    },
                )

        type_of_work_records = {}
        for name, point, redo_point, major_changes_point, minor_changes_point in type_of_work_seed:
            record = TypeOfWork.objects.create(
                work_type_name=name,
                point=point,
                redo_point=redo_point,
                major_changes_point=major_changes_point,
                minor_changes_point=minor_changes_point,
            )
            type_of_work_records[name] = record

        service_category_records = {}
        for name, description in service_categories_seed:
            record = ServiceCategory.objects.create(name=name, description=description)
            service_category_records[name] = record

        brand_records = {}
        client_records = {}
        for item in client_seed:
            brand = Brand.objects.create(name=item["name"])
            brand_records[item["name"]] = brand
            client = Client.objects.create(
                name=item["name"],
                client_interface=item["client_interface"],
                client_interface_contact_number=item["contact"],
                accent_color=item["accent_color"],
            )
            client_records[item["name"]] = client
            attach_file(
                client.attachments.create().file,
                f"{client.name.lower().replace(' ', '_')}_brief.txt",
                f"Dummy attachment for {client.name}\nPrimary interface: {client.client_interface}\n",
            )

        client_attachment_objects = list(ClientAttachment.objects.select_related("client"))
        for attachment in client_attachment_objects:
            self.stdout.write(f"Created client attachment for: {attachment.client.name}")

        owner_seed = [
            ("rhea_planner", "Web Packaging Solution"),
            ("rhea_planner", "James Douglas India"),
            ("rhea_planner", "Ema Partners"),
            ("arjun_planner", "Unifab"),
            ("arjun_planner", "TVS Rubber"),
            ("arjun_planner", "Web Packaging Solution"),
        ]
        for user_key, client_name in owner_seed:
            ClientOwner.objects.create(user=users[user_key], client=client_records[client_name])

        reporting_months = [date(2026, 1, 1), date(2026, 2, 1), date(2026, 3, 1)]
        for item in client_seed:
            client = client_records[item["name"]]
            for month_date, amount in zip(reporting_months, item["monthly_amounts"]):
                ClientMonthlyAmount.objects.create(client=client, date=month_date, amt=amount)

        scope_records = {}
        for item in scope_seed:
            scope = ScopeOfWork.objects.create(
                client=client_records[item["client"]],
                service_category=service_category_records[item["service_category"]],
                deliverable_name=item["deliverable_name"],
                description=item["description"],
                total_unit=item["total_unit"],
            )
            scope.type_of_work.set([type_of_work_records[name] for name in item["type_of_work"]])
            scope_records[item["deliverable_name"]] = scope

        remark_records = {}
        for name, description, point in negative_remarks_seed:
            remark_records[name] = NegativeRemark.objects.create(
                remark_name=name,
                description=description,
                point=point,
            )

        group_seed = {
            "Design Studio": ["ava_designer", "liam_creative", "maya_visuals", "noah_motion"],
            "Planning Cell": ["rhea_planner", "arjun_planner"],
            "Creative Review": ["aditya_art", "megha_art", "rhea_planner", "arjun_planner"],
        }
        for group_name, members in group_seed.items():
            group = Group.objects.create(name=group_name)
            for member_key in members:
                GroupMember.objects.create(group=group, user=users[member_key])

        stage_records = {}
        for stage_value, label in stage_mapping.items():
            stage_records[stage_value] = TaskStage.objects.create(name=label)

        def build_task_defaults(item, designer_key, target_date_value, stage_value):
            return {
                "client": client_records[item["client"]],
                "scope_of_work": scope_records[item["scope"]],
                "task_name": item["task_name"],
                "instructions": item["instructions"],
                "InstructionsByArtDirector": item["art_instructions"],
                "priority": item["priority"],
                "stage": stage_value,
                "designer": users[designer_key],
                "type_of_work": type_of_work_records[item["type_of_work"]],
                "platform": item["platform"],
                "created_by": users[item["created_by"]],
                "target_date": target_date_value,
                "slides": item["slides"],
                "impressions": item["impressions"],
                "ctr": item["ctr"],
                "engagement_rate": item["engagement_rate"],
                "promotion_type": item["promotion_type"],
                "have_major_changes": item.get("have_major_changes", False),
                "have_minor_changes": item.get("have_minor_changes", False),
                "excellence": item.get("excellence"),
                "excellence_reason": item.get("excellence_reason", ""),
            }

        created_tasks = []

        for item in task_seed:
            task = Task.objects.create(**build_task_defaults(item, item["designer"], item["target_date"], item["stage"]))
            created_tasks.append(task)
            sync_stage_link(task, stage_records)

            for remark_name in item["negative_remarks"]:
                NegativeRemarkOnTask.objects.create(task=task, negative_remark=remark_records[remark_name])

            attachment_name = f"task_{task.id}_{task.task_name.lower().replace(' ', '_')}.txt"
            attach_file(
                task.attachments.create().file,
                attachment_name,
                f"Task attachment for {task.task_name}\nClient: {task.client.name}\nStage: {task.get_stage_display()}\n",
            )

            for revision_data in item["revisions"]:
                revision = Task.objects.create(
                    revision_of=task,
                    revision_no=revision_data["revision_no"],
                    revision_type=revision_data["revision_type"],
                    **build_task_defaults(item, revision_data["designer"], revision_data["target_date"], revision_data["stage"]),
                )
                created_tasks.append(revision)
                sync_stage_link(revision, stage_records)

            for redo_data in item["redos"]:
                redo = Task.objects.create(
                    redo_of=task,
                    redo_no=redo_data["redo_no"],
                    **build_task_defaults(item, redo_data["designer"], redo_data["target_date"], redo_data["stage"]),
                )
                created_tasks.append(redo)
                sync_stage_link(redo, stage_records)

        if bulk_tasks:
            client_names = list(client_records.keys())
            designer_keys = ["ava_designer", "liam_creative", "maya_visuals", "noah_motion"]
            work_type_names = list(type_of_work_records.keys())
            platform_values = ["", Task.Platform.INSTAGRAM, Task.Platform.LINKEDIN, Task.Platform.FACEBOOK]
            for index in range(1, bulk_tasks + 1):
                client_name = client_names[(index - 1) % len(client_names)]
                work_type_name = work_type_names[(index - 1) % len(work_type_names)]
                stage_value = list(stage_mapping.keys())[index % len(stage_mapping)]
                task = Task.objects.create(
                    client=client_records[client_name],
                    scope_of_work=next(
                        scope
                        for scope in scope_records.values()
                        if scope.client_id == client_records[client_name].id
                    ),
                    task_name=f"Bulk Seed Task {index:03d}",
                    instructions=f"Bulk seeded task {index:03d} for pagination and QA.",
                    InstructionsByArtDirector="Use the existing system and keep consistency.",
                    priority=[Task.Priority.HIGH, Task.Priority.MEDIUM, Task.Priority.LOW][index % 3],
                    stage=stage_value,
                    designer=users[designer_keys[index % len(designer_keys)]],
                    type_of_work=type_of_work_records[work_type_name],
                    platform=platform_values[index % len(platform_values)],
                    created_by=users["rhea_planner" if index % 2 == 0 else "arjun_planner"],
                    target_date=date(2026, 3, (index % 28) + 1),
                    slides=(index % 10) + 1,
                    impressions=index * 100,
                    ctr=Decimal(f"{(index % 7) + 0.25:.2f}"),
                    engagement_rate=Decimal(f"{(index % 9) + 0.50:.2f}"),
                    promotion_type=Task.PromotionType.SPONSORED if index % 2 == 0 else Task.PromotionType.ORGANIC,
                )
                sync_stage_link(task, stage_records)
                created_tasks.append(task)

        created_tasks.sort(
            key=lambda task: (
                task.client.name if task.client_id else "",
                stage_style_rank.get(task.stage, 99),
                task.task_name,
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Seed complete: "
                f"{len(users)} users, "
                f"{Employee.objects.count()} employee profiles, "
                f"{Brand.objects.count()} brands, "
                f"{Client.objects.count()} clients, "
                f"{ClientOwner.objects.count()} client owners, "
                f"{ClientMonthlyAmount.objects.count()} monthly amounts, "
                f"{Group.objects.count()} groups, "
                f"{GroupMember.objects.count()} group members, "
                f"{ServiceCategory.objects.count()} service categories, "
                f"{TypeOfWork.objects.count()} types of work, "
                f"{ScopeOfWork.objects.count()} scope items, "
                f"{NegativeRemark.objects.count()} negative remarks, "
                f"{NegativeRemarkOnTask.objects.count()} task remark links, "
                f"{ClientAttachment.objects.count()} client attachments, "
                f"{TaskAttachment.objects.count()} task attachments, "
                f"{TaskStage.objects.count()} task stages, "
                f"{Task.objects.count()} tasks, "
                f"{TaskOnStage.objects.count()} task stage links."
            )
        )
