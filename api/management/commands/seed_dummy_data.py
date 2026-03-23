from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from api.models import Brand, Client, ClientOwner, ScopeOfWork, ServiceCategory, Task


class Command(BaseCommand):
    help = "Seed dummy users, brands, clients, scope of work, tasks, and task revisions."

    def add_arguments(self, parser):
        parser.add_argument(
            "--bulk-tasks",
            type=int,
            default=0,
            help="Create additional pagination test tasks.",
        )

    def handle(self, *args, **options):
        bulk_tasks = max(0, options["bulk_tasks"])
        user_model = get_user_model()
        pivot_client_names = [
            "shinhan bank",
            "ema partners",
            "avant",
            "JSK",
            "Adtiya birla fashion and Lifestyle",
            "selkies",
            "andromeda",
            "tvs rubber",
            "james douglas india",
            "james douglas UAE",
            "james douglas Global",
        ]

        users_seed = [
            {"key": "ava_designer", "email": "ava@pivot.test", "first_name": "Ava", "last_name": "Shaw", "role": user_model.Role.DESIGNER},
            {"key": "liam_creative", "email": "liam@pivot.test", "first_name": "Liam", "last_name": "Cole", "role": user_model.Role.DESIGNER},
            {"key": "maya_visuals", "email": "maya@pivot.test", "first_name": "Maya", "last_name": "Rao", "role": user_model.Role.DESIGNER},
            {"key": "noah_motion", "email": "noah@pivot.test", "first_name": "Noah", "last_name": "Kerr", "role": user_model.Role.DESIGNER},
            {"key": "rhea_planner", "email": "rhea@pivot.test", "first_name": "Rhea", "last_name": "Kapoor", "role": user_model.Role.ACCOUNT_PLANNER},
            {"key": "arjun_planner", "email": "arjun@pivot.test", "first_name": "Arjun", "last_name": "Mehta", "role": user_model.Role.ACCOUNT_PLANNER},
        ]

        users = {}
        for data in users_seed:
            user, created = user_model.objects.get_or_create(
                email=data["email"],
                defaults={
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "role": data["role"],
                },
            )
            users[data["key"]] = user
            self.stdout.write(f"{'Created' if created else 'Exists'} user: {user.email}")

        deleted_revision_tasks, _ = Task.objects.filter(revision_of__isnull=False).delete()
        deleted_original_tasks, _ = Task.objects.filter(revision_of__isnull=True).delete()
        deleted_ownerships, _ = ClientOwner.objects.all().delete()
        deleted_scope_items, _ = ScopeOfWork.objects.all().delete()
        deleted_clients, _ = Client.objects.all().delete()
        deleted_brands, _ = Brand.objects.all().delete()
        self.stdout.write(
            "Deleted existing client data: "
            f"{deleted_revision_tasks + deleted_original_tasks} tasks, {deleted_ownerships} ownerships, "
            f"{deleted_scope_items} scope items, {deleted_clients} clients, {deleted_brands} brands."
        )

        brand_names = pivot_client_names
        for name in brand_names:
            brand = Brand.objects.create(name=name)
            self.stdout.write(f"Created brand: {brand.name}")

        clients_seed = [
            {"name": "shinhan bank", "client_interface": "Aarti Nair", "client_interface_contact_number": "+91-9900011111"},
            {"name": "ema partners", "client_interface": "Kabir Shah", "client_interface_contact_number": "+91-9900011112"},
            {"name": "avant", "client_interface": "Neha Suri", "client_interface_contact_number": "+91-9900011113"},
            {"name": "JSK", "client_interface": "Rohan Patel", "client_interface_contact_number": "+91-9900011114"},
            {"name": "Adtiya birla fashion and Lifestyle", "client_interface": "Ishita Mehra", "client_interface_contact_number": "+91-9900011115"},
            {"name": "selkies", "client_interface": "Tanya Arora", "client_interface_contact_number": "+91-9900011116"},
            {"name": "andromeda", "client_interface": "Varun Khanna", "client_interface_contact_number": "+91-9900011117"},
            {"name": "tvs rubber", "client_interface": "Siddharth Rao", "client_interface_contact_number": "+91-9900011118"},
            {"name": "james douglas india", "client_interface": "Megha Bhasin", "client_interface_contact_number": "+91-9900011119"},
            {"name": "james douglas UAE", "client_interface": "Farah Khan", "client_interface_contact_number": "+91-9900011120"},
            {"name": "james douglas Global", "client_interface": "Aman Dutta", "client_interface_contact_number": "+91-9900011121"},
        ]

        clients = {}
        for item in clients_seed:
            client = Client.objects.create(
                name=item["name"],
                client_interface=item["client_interface"],
                client_interface_contact_number=item["client_interface_contact_number"],
            )
            clients[item["name"]] = client
            self.stdout.write(f"Created client: {client.name}")

        client_owner_seed = [
            ("rhea_planner", "shinhan bank"),
            ("rhea_planner", "ema partners"),
            ("rhea_planner", "avant"),
            ("rhea_planner", "JSK"),
            ("rhea_planner", "selkies"),
            ("rhea_planner", "james douglas india"),
            ("arjun_planner", "shinhan bank"),
            ("arjun_planner", "ema partners"),
            ("arjun_planner", "Adtiya birla fashion and Lifestyle"),
            ("arjun_planner", "andromeda"),
            ("arjun_planner", "tvs rubber"),
            ("arjun_planner", "james douglas UAE"),
            ("arjun_planner", "james douglas Global"),
        ]

        for user_key, client_name in client_owner_seed:
            ownership = ClientOwner.objects.create(
                user=users[user_key],
                client=clients[client_name],
            )
            self.stdout.write(
                f"Created client owner: {ownership.user.email} -> {ownership.client.name}"
            )

        sow_seed = [
            {
                "client": "shinhan bank",
                "service_category": ["Performance Marketing"],
                "deliverable_name": "Retail Credit Card Campaign Ads",
                "description": "Paid campaign creatives for seasonal card acquisition and branch-led promotions.",
                "total_unit": 12,
            },
            {
                "client": "shinhan bank",
                "service_category": ["Brand Collateral"],
                "deliverable_name": "Branch Communication Collateral",
                "description": "Poster, standee, leaflet, and in-branch awareness materials.",
                "total_unit": 8,
            },
            {
                "client": "ema partners",
                "service_category": ["Website Development"],
                "deliverable_name": "Leadership Microsite Assets",
                "description": "Visual system and page assets for executive search campaign landing pages.",
                "total_unit": 6,
            },
            {
                "client": "ema partners",
                "service_category": ["Social Media Management"],
                "deliverable_name": "Employer Branding Social Pack",
                "description": "LinkedIn-first social creative set for thought leadership and hiring visibility.",
                "total_unit": 10,
            },
            {
                "client": "avant",
                "service_category": ["Brand Guide"],
                "deliverable_name": "Brand Refresh Guidelines",
                "description": "Updated tone, typography, and visual expression guide for campaign rollout.",
                "total_unit": 1,
            },
            {
                "client": "avant",
                "service_category": ["Performance Marketing"],
                "deliverable_name": "Conversion Ad Creative Suite",
                "description": "Static and motion assets tailored for high-intent performance funnels.",
                "total_unit": 14,
            },
            {
                "client": "JSK",
                "service_category": ["Brand Collateral"],
                "deliverable_name": "Corporate Presentation Templates",
                "description": "Sales deck, capability deck, and business presentation layouts.",
                "total_unit": 4,
            },
            {
                "client": "JSK",
                "service_category": ["Social Media Management"],
                "deliverable_name": "Monthly Social Calendar",
                "description": "Platform-specific social creatives for product and announcement content.",
                "total_unit": 16,
            },
            {
                "client": "Adtiya birla fashion and Lifestyle",
                "service_category": ["Brand Collateral"],
                "deliverable_name": "Retail Launch Collateral",
                "description": "In-store launch assets, event branding, and shopper communication materials.",
                "total_unit": 12,
            },
            {
                "client": "Adtiya birla fashion and Lifestyle",
                "service_category": ["Social Media Management"],
                "deliverable_name": "Fashion Campaign Social Kit",
                "description": "Launch creatives across reels, stories, statics, and influencer support formats.",
                "total_unit": 20,
            },
            {
                "client": "selkies",
                "service_category": ["Brand Logo"],
                "deliverable_name": "Collection Identity Explorations",
                "description": "Sub-brand logo explorations and visual motifs for new collection drops.",
                "total_unit": 2,
            },
            {
                "client": "selkies",
                "service_category": ["Social Media Management"],
                "deliverable_name": "Campaign Social Storytelling Pack",
                "description": "Narrative-led post, story, and reel creatives for monthly launches.",
                "total_unit": 14,
            },
            {
                "client": "andromeda",
                "service_category": ["Website Development"],
                "deliverable_name": "Product Landing Page Graphics",
                "description": "Hero visuals and section artwork for product and campaign landing pages.",
                "total_unit": 8,
            },
            {
                "client": "andromeda",
                "service_category": ["SEO"],
                "deliverable_name": "SEO Editorial Design Support",
                "description": "Feature visuals and infographic snippets for organic content publishing.",
                "total_unit": 12,
            },
            {
                "client": "tvs rubber",
                "service_category": ["Performance Marketing"],
                "deliverable_name": "Dealer Network Lead Ads",
                "description": "Regional performance creatives for dealer and distributor acquisition.",
                "total_unit": 15,
            },
            {
                "client": "tvs rubber",
                "service_category": ["Brand Collateral"],
                "deliverable_name": "Trade Marketing Kit",
                "description": "Catalog pages, trade fair panels, and product benefit sell sheets.",
                "total_unit": 6,
            },
            {
                "client": "james douglas india",
                "service_category": ["Performance Marketing"],
                "deliverable_name": "India Market Paid Creative Set",
                "description": "Localized ad creatives for acquisition campaigns in the India market.",
                "total_unit": 10,
            },
            {
                "client": "james douglas india",
                "service_category": ["Social Media Management"],
                "deliverable_name": "India Social Calendar",
                "description": "Localized social creative lineup for monthly product and thought leadership content.",
                "total_unit": 12,
            },
            {
                "client": "james douglas UAE",
                "service_category": ["Performance Marketing"],
                "deliverable_name": "UAE Regional Ad Creatives",
                "description": "Performance assets tailored for UAE promotions and lead-generation campaigns.",
                "total_unit": 10,
            },
            {
                "client": "james douglas UAE",
                "service_category": ["Brand Collateral"],
                "deliverable_name": "Regional Sales Collateral",
                "description": "Presentation kits, one-pagers, and proposal assets for UAE market outreach.",
                "total_unit": 5,
            },
            {
                "client": "james douglas Global",
                "service_category": ["Website Development"],
                "deliverable_name": "Global Website Asset Library",
                "description": "Reusable design assets for global web properties and campaign pages.",
                "total_unit": 9,
            },
            {
                "client": "james douglas Global",
                "service_category": ["Brand Guide"],
                "deliverable_name": "Global Brand Governance Toolkit",
                "description": "Master brand governance deck for international campaign consistency.",
                "total_unit": 1,
            },
        ]

        for item in sow_seed:
            client = clients[item["client"]]
            category_name = item["service_category"][0]
            service_category, _ = ServiceCategory.objects.get_or_create(
                name=category_name,
                defaults={"description": ""},
            )
            sow, created = ScopeOfWork.objects.get_or_create(
                client=client,
                deliverable_name=item["deliverable_name"],
                defaults={
                    "service_category": service_category,
                    "description": item["description"],
                    "total_unit": item["total_unit"],
                },
            )
            if not created:
                updated = False
                if sow.service_category_id != service_category.id:
                    sow.service_category = service_category
                    updated = True
                for attr in ["description", "total_unit"]:
                    if getattr(sow, attr) != item[attr]:
                        setattr(sow, attr, item[attr])
                        updated = True
                if updated:
                    sow.save()

            self.stdout.write(f"{'Created' if created else 'Exists'} scope item: {sow.client.name} | {sow.deliverable_name}")

        def build_march_2026_task_seed():
            client_order = pivot_client_names
            designer_order = [
                "ava_designer",
                "liam_creative",
                "maya_visuals",
                "noah_motion",
            ]
            priorities = [
                Task.Priority.HIGH,
                Task.Priority.MEDIUM,
                Task.Priority.LOW,
            ]
            concepts = [
                (
                    "Campaign Key Visuals",
                    "Build a primary campaign KV with resize variations for social and print placements.",
                ),
                (
                    "Landing Page Graphics",
                    "Design hero and supporting website sections aligned to the monthly campaign theme.",
                ),
                (
                    "Packaging Mockups",
                    "Create polished packaging mockups with material and finish explorations.",
                ),
                (
                    "Product Reel Storyboards",
                    "Storyboard a short motion-led launch reel with scene directions and frame references.",
                ),
                (
                    "Retail Display Concepts",
                    "Prepare point-of-sale display concepts for store rollout and merchandising review.",
                ),
                (
                    "Performance Ad Set",
                    "Create static and motion ad creatives for conversion-focused media buying.",
                ),
                (
                    "Festival Social Pack",
                    "Develop post, story, and reel layouts for the seasonal social media calendar.",
                ),
                (
                    "Email Banner Series",
                    "Design modular email headers and promo banners for CRM campaign drops.",
                ),
            ]

            month_start = date(2026, 3, 1)
            month_end = date(2026, 3, 31)
            seed = []
            task_index = 0
            current_day = month_start

            while current_day <= month_end:
                if current_day.weekday() == 6:
                    current_day += timedelta(days=1)
                    continue

                for client_index, client_name in enumerate(client_order):
                    concept_title, concept_instruction = concepts[task_index % len(concepts)]
                    designer_key = designer_order[task_index % len(designer_order)]
                    priority = priorities[task_index % len(priorities)]
                    planner_completed = task_index % 5 == 0
                    art_director_completed = task_index % 3 == 0 or planner_completed
                    designer_completed = task_index % 2 == 0 or art_director_completed
                    revisions = [
                        {
                            "designer": designer_order[(task_index + 1) % len(designer_order)],
                            "priority": priorities[(task_index + 1) % len(priorities)],
                            "is_marked_completed_by_account_planner": False,
                            "is_marked_completed_by_art_director": False,
                            "is_marked_completed_by_designer": (task_index % 2 == 0),
                        }
                    ]

                    if (task_index + client_index) % 3 == 0:
                        revisions.append(
                            {
                                "designer": designer_order[(task_index + 2) % len(designer_order)],
                                "priority": priorities[(task_index + 2) % len(priorities)],
                                "is_marked_completed_by_account_planner": (task_index % 2 == 0),
                                "is_marked_completed_by_art_director": (task_index % 2 == 0),
                                "is_marked_completed_by_designer": True,
                            }
                        )

                    seed.append(
                        {
                            "client": client_name,
                            "designer": designer_key,
                            "task_name": f"{client_name} - March 2026 Day {current_day.day:02d} - {concept_title}",
                            "instructions": (
                                f"{concept_instruction} Scheduled for {current_day.isoformat()} "
                                f"for {client_name}."
                            ),
                            "priority": priority,
                            "target_date": current_day + timedelta(days=2),
                            "is_marked_completed_by_account_planner": planner_completed,
                            "is_marked_completed_by_art_director": art_director_completed,
                            "is_marked_completed_by_designer": designer_completed,
                            "revisions": [
                                {
                                    **revision,
                                    "target_date": (current_day + timedelta(days=1 + revision_index)),
                                }
                                for revision_index, revision in enumerate(revisions)
                            ],
                        }
                    )
                    task_index += 1

                current_day += timedelta(days=1)

            return seed

        task_seed = build_march_2026_task_seed()

        created_tasks = 0
        created_revisions = 0
        created_bulk_tasks = 0
        created_bulk_revisions = 0

        for item in task_seed:
            client = clients[item["client"]]
            designer = users[item["designer"]]

            task = (
                Task.objects.filter(
                    client=client,
                    task_name=item["task_name"],
                    revision_of__isnull=True,
                )
                .order_by("id")
                .first()
            )
            created = task is None

            if created:
                task = Task.objects.create(
                    client=client,
                    task_name=item["task_name"],
                    target_date=item["target_date"],
                    instructions=item["instructions"],
                    priority=item["priority"],
                    designer=designer,
                    is_marked_completed_by_account_planner=item["is_marked_completed_by_account_planner"],
                    is_marked_completed_by_art_director=item["is_marked_completed_by_art_director"],
                    is_marked_completed_by_designer=item["is_marked_completed_by_designer"],
                )
                created_tasks += 1
            else:
                updated = False
                for attr, value in [
                    ("instructions", item["instructions"]),
                    ("priority", item["priority"]),
                    ("designer", designer),
                    ("target_date", item["target_date"]),
                    ("is_marked_completed_by_account_planner", item["is_marked_completed_by_account_planner"]),
                    ("is_marked_completed_by_art_director", item["is_marked_completed_by_art_director"]),
                    ("is_marked_completed_by_designer", item["is_marked_completed_by_designer"]),
                ]:
                    if getattr(task, attr) != value:
                        setattr(task, attr, value)
                        updated = True
                if updated:
                    task.save()

            self.stdout.write(f"{'Created' if created else 'Exists'} task: {task.task_name}")

            for index, revision_data in enumerate(item["revisions"], start=1):
                revision_defaults = {
                    "client": client,
                    "designer": users[revision_data["designer"]],
                    "task_name": task.task_name,
                    "instructions": f"Revision pass {index} for: {item['instructions']}",
                    "priority": revision_data["priority"],
                    "target_date": revision_data["target_date"],
                    "is_marked_completed_by_account_planner": revision_data["is_marked_completed_by_account_planner"],
                    "is_marked_completed_by_art_director": revision_data["is_marked_completed_by_art_director"],
                    "is_marked_completed_by_designer": revision_data["is_marked_completed_by_designer"],
                }

                revision = Task.objects.filter(revision_of=task, revision_no=index).order_by("id").first()
                rev_created = revision is None

                if rev_created:
                    revision = Task.objects.create(revision_of=task, revision_no=index, **revision_defaults)
                    created_revisions += 1
                else:
                    updated = False
                    for attr, value in revision_defaults.items():
                        if getattr(revision, attr) != value:
                            setattr(revision, attr, value)
                            updated = True
                    if updated:
                        revision.save()

                self.stdout.write(
                    f"{'Created' if rev_created else 'Exists'} revision: "
                    f"{revision.task_name} (original #{task.id})"
                )

        if bulk_tasks:
            client_order = list(clients.values())
            user_order = [users["ava_designer"], users["liam_creative"], users["maya_visuals"], users["noah_motion"]]
            priorities = [Task.Priority.HIGH, Task.Priority.MEDIUM, Task.Priority.LOW]
            creative_types = [
                "Social Ad Set",
                "Packaging Concept",
                "Landing Page Hero",
                "Product Story Reel",
                "Billboard Visual",
                "Email Banner Series",
                "Retail Standee Design",
            ]

            for index in range(1, bulk_tasks + 1):
                client = client_order[(index - 1) % len(client_order)]
                designer = user_order[(index - 1) % len(user_order)]
                priority = priorities[(index - 1) % len(priorities)]
                creative_type = creative_types[(index - 1) % len(creative_types)]
                title = f"Pagination Test Task {index:03d} - {creative_type}"
                target_date = date(2026, 3, min(index, 28))
                planner_completed = index % 5 == 0
                art_director_completed = index % 3 == 0 or planner_completed
                designer_completed = index % 2 == 0 or art_director_completed

                task, task_created = Task.objects.get_or_create(
                    client=client,
                    task_name=title,
                    revision_of__isnull=True,
                    defaults={
                        "instructions": f"Create {creative_type.lower()} for campaign wave {index:03d}.",
                        "priority": priority,
                        "designer": designer,
                        "target_date": target_date,
                        "is_marked_completed_by_account_planner": planner_completed,
                        "is_marked_completed_by_art_director": art_director_completed,
                        "is_marked_completed_by_designer": designer_completed,
                    },
                )

                if task_created:
                    created_bulk_tasks += 1

                if index % 4 == 0:
                    rev_index = 1
                    _, rev_created = Task.objects.get_or_create(
                        revision_of=task,
                        revision_no=rev_index,
                        defaults={
                            "client": client,
                            "task_name": task.task_name,
                            "instructions": f"Revision pass {rev_index} for pagination test task {index:03d}.",
                            "priority": priority,
                            "designer": designer,
                            "target_date": target_date + timedelta(days=1),
                            "is_marked_completed_by_account_planner": False,
                            "is_marked_completed_by_art_director": False,
                            "is_marked_completed_by_designer": True,
                        },
                    )
                    if rev_created:
                        created_bulk_revisions += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Bulk seed complete. New bulk tasks: {created_bulk_tasks}, "
                    f"new bulk revisions: {created_bulk_revisions}."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete. New tasks: {created_tasks}, new revisions: {created_revisions}, "
                f"new bulk tasks: {created_bulk_tasks}, new bulk revisions: {created_bulk_revisions}."
            )
        )
