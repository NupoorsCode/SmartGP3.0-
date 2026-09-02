# -*- coding: utf-8 -*-
"""SmartGP content model.

Single source of truth. Prices, strengths and availability are defined once
here and read by the treatment pages, the pricing page, the comparison table
and the Product/Offer structured data — so those surfaces cannot disagree.
"""

ORIGIN = "https://smartgp.co.uk"

BRAND = {
    "name": "SmartGP",
    "tagline": "Private online weight loss service · United Kingdom",
    "company": "Smartway Pharma Limited",
    "company_no": "[company number]",
    "office": "SmartRx Pharmacy, 10 Lyon Road, London SW19 2RL, United Kingdom",
    "gphc": "[GPhC premises number]",
    "superintendent": "Vinesh [surname]",
    "superintendent_reg": "[GPhC registration number]",
    "cqc": "[CQC provider ID] — registration position pending (DEC-03)",
    "phone": "[clinic telephone]",
    "email": "hello@smartgp.co.uk",
}

# Primary navigation follows the BRD (Section 7.4): Clinic, Learn, Support,
# Contact us. "Clinic" is the hub for treatments, pricing and the team.
NAV = [
    ("/treatments/", "Clinic"),
    ("/learn/", "Learn"),
    ("/support/", "Support"),
    ("/contact/", "Contact us"),
]

FOOTER_NAV = [
    ("Clinic", [
        ("/treatments/", "Treatments"),
        ("/treatments/mounjaro-tirzepatide/", "Mounjaro (tirzepatide)"),
        ("/treatments/wegovy-semaglutide-injection/", "Wegovy injection"),
        ("/pricing/", "Pricing"),
        ("/consultation/", "Start a consultation"),
    ]),
    ("About us", [
        ("/about/", "About SmartGP"),
        ("/about/team/", "Meet the team"),
        ("/about/testimonials/", "Testimonials"),
        ("/about/careers/", "Careers"),
        ("/contact/", "Contact us"),
    ]),
    ("Support", [
        ("/support/", "FAQ and advice"),
        ("/support/patient-resources/", "Patient resources"),
        ("/learn/", "Learn about weight loss"),
        ("/legal/complaints/", "Complaints procedure"),
        ("/legal/accessibility/", "Accessibility statement"),
    ]),
    ("Legal", [
        ("/legal/terms/", "Terms and conditions"),
        ("/legal/privacy/", "Privacy policy"),
        ("/legal/cookies/", "Cookie policy"),
        ("/sitemap.xml", "Sitemap"),
    ]),
]

EMERGENCY = {
    "title": "Please do not use this service for medical emergencies",
    "lead": "If you or someone else has life-threatening symptoms, call 999 or go "
            "to A&E immediately.",
    "items": [
        "Chest pain, severe breathlessness, or symptoms of a heart attack",
        "Signs of a stroke, such as facial drooping, arm weakness, speech difficulty, or sudden confusion",
        "Severe allergic reaction, including swelling of the face, lips or tongue, or difficulty breathing",
        "Loss of consciousness, seizure, or severe head injury",
        "Severe bleeding, major injury, or suspected fracture",
        "Severe abdominal pain, sudden severe headache, or collapse",
        "Suicidal thoughts, risk of self-harm, or immediate risk to others",
    ],
    "nhs": "For urgent but non-emergency concerns, contact NHS 111 or your own GP practice.",
}

# --------------------------------------------------------------- clinicians
TEAM = [
    {
        "slug": "rachel-wood",
        "name": "Rachel Wood",
        "initials": "RW",
        "role": "Clinical lead and responsible prescriber",
        "reg": "GPhC [registration number]",
        "about": "Rachel leads the clinical service at SmartGP and sees patients "
                 "herself. She has worked in community and primary care pharmacy "
                 "for over a decade and prescribes in weight management. She signs "
                 "off every questionnaire before it goes live.",
        "responsibilities": "Clinical governance, questionnaire sign-off, prescribing, "
                            "and reviewing the clinical content published on this site.",
        "interest": "Medical weight management, GLP-1 therapy, cardiovascular risk",
        "quals": "MPharm, Independent Prescriber",
        "interests": "Long-distance running, and a stubborn allotment.",
    },
    {
        "slug": "vinesh",
        "name": "Vinesh [surname]",
        "initials": "V",
        "role": "Superintendent Pharmacist",
        "reg": "GPhC [registration number]",
        "about": "Vinesh is the Superintendent Pharmacist for Smartway Pharma "
                 "Limited and is legally accountable for how medicines are "
                 "dispensed and supplied across SmartRx and SmartGP. He also sees "
                 "patients as a prescriber.",
        "responsibilities": "Supply model, premises registration, record-keeping, "
                            "cold chain governance and verification evidence.",
        "interest": "Distance supply governance, cold chain, patient safety",
        "quals": "MPharm, MRPharmS, Independent Prescriber",
        "interests": "Cricket, and rebuilding an old motorbike very slowly.",
    },
    {
        "slug": "josh-cocklin",
        "name": "Josh Cocklin",
        "initials": "JC",
        "role": "Chief Executive and legal adviser",
        "reg": "Solicitor, England and Wales",
        "about": "Josh signs off the clinical and legal wording used across the "
                 "site, including the terms, the privacy policy and every consent "
                 "statement in the consultation.",
        "responsibilities": "Terms and conditions, privacy and cookie policies, "
                            "advertising compliance and complaints handling.",
        "interest": "Healthcare regulation, advertising compliance, data protection",
        "quals": "LLB, Solicitor",
        "interests": "Sailing, and an unreasonable number of cookbooks.",
    },
]

# ------------------------------------------------------------ questionnaire
GLP1_MODULE = [
    {"k": "mtc", "type": "radio",
     "label": "Do you, or does anyone in your family, have a history of medullary thyroid carcinoma or multiple endocrine neoplasia type 2 (MEN 2)?",
     "options": ["No", "Yes", "I am not sure"], "required": True,
     "hint": "A rare thyroid cancer and a related inherited condition. Your GP would have told you if this applied.",
     "flag": {"when": ["Yes", "I am not sure"], "level": "exclusion",
              "note": "Absolute contraindication for GLP-1 therapy"}},
    {"k": "pancreatitis", "type": "radio",
     "label": "Have you ever had pancreatitis (inflammation of the pancreas)?",
     "options": ["No", "Yes", "I am not sure"], "required": True,
     "flag": {"when": ["Yes", "I am not sure"], "level": "exclusion",
              "note": "Absolute contraindication for GLP-1 therapy"}},
    {"k": "type1", "type": "radio",
     "label": "Have you been diagnosed with type 1 diabetes?",
     "options": ["No", "Yes", "I have type 2 diabetes"], "required": True,
     "flag": {"when": ["Yes"], "level": "exclusion",
              "note": "GLP-1 agents are not indicated in type 1 diabetes"}},
    {"k": "pregnancy", "type": "radio",
     "label": "Are you currently pregnant, breastfeeding, or planning a pregnancy in the next 12 months?",
     "options": ["None of these", "Pregnant", "Breastfeeding", "Planning a pregnancy"],
     "required": True, "showIf": {"k": "sexAtBirth", "is": "Female"},
     "flag": {"when": ["Pregnant", "Breastfeeding", "Planning a pregnancy"],
              "level": "exclusion", "note": "Absolute contraindication"}},
    {"k": "currentGlp1", "type": "radio",
     "label": "Are you currently taking any other GLP-1 treatment?",
     "options": ["No", "Yes"], "required": True,
     "flag": {"when": ["Yes"], "level": "caution",
              "note": "Cannot be combined — clinician to confirm dose and switch plan"}},
    {"k": "currentDose", "type": "text",
     "label": "If you are switching or restarting, what dose are you on now?",
     "placeholder": "e.g. Mounjaro 5 mg weekly",
     "showIf": {"k": "currentGlp1", "is": "Yes"}, "required": True},
    {"k": "gi", "type": "checkboxes", "label": "Do any of these apply to you?",
     "options": ["Gastroparesis (delayed stomach emptying)", "Inflammatory bowel disease",
                 "Severe or persistent vomiting", "Previous bariatric or stomach surgery",
                 "None of these"],
     "required": True, "exclusive": "None of these",
     "flag": {"whenAnyExcept": "None of these", "level": "caution",
              "note": "Severe gastrointestinal condition — material to prescribing"}},
    {"k": "allergies", "type": "textarea", "label": "Do you have any known allergies?",
     "placeholder": "Medicines, foods, latex — or type \u201cnone\u201d", "required": True},
]

ORLISTAT_MODULE = [
    {"k": "malabsorption", "type": "radio",
     "label": "Have you been diagnosed with chronic malabsorption syndrome or cholestasis?",
     "options": ["No", "Yes", "I am not sure"], "required": True,
     "flag": {"when": ["Yes", "I am not sure"], "level": "exclusion",
              "note": "Contraindicated for orlistat"}},
    {"k": "pregnancy", "type": "radio",
     "label": "Are you currently pregnant, breastfeeding, or planning a pregnancy?",
     "options": ["None of these", "Pregnant", "Breastfeeding", "Planning a pregnancy"],
     "required": True, "showIf": {"k": "sexAtBirth", "is": "Female"},
     "flag": {"when": ["Pregnant", "Breastfeeding"], "level": "exclusion",
              "note": "Not suitable in pregnancy or breastfeeding"}},
    {"k": "ciclosporin", "type": "radio",
     "label": "Do you take ciclosporin, warfarin, levothyroxine or any anti-epileptic medicine?",
     "options": ["No", "Yes"], "required": True,
     "flag": {"when": ["Yes"], "level": "caution", "note": "Known interaction — clinician to review"}},
    {"k": "allergies", "type": "textarea", "label": "Do you have any known allergies?",
     "placeholder": "Medicines, foods, latex — or type \u201cnone\u201d", "required": True},
]

ADVICE_MODULE = [
    {"k": "reason", "type": "textarea",
     "label": "What would you like to discuss with the clinician?", "required": True},
]

# ----------------------------------------------------------------- services
SERVICES = [
    {
        "id": "advice-consultation",
        "kind": "service",
        "name": "Advice-only consultation",
        "short": "Advice consultation",
        "strapline": "Talk it through first — no medicine supplied",
        "blurb": "A 20-minute video appointment with a clinician to discuss your "
                 "options, your history and whether medical weight management is "
                 "right for you. No prescription is issued from this appointment.",
        "inn": None,
        "price_from": 10,
        "published": True,
        "decision": "DEC-04",
        "strengths": [{"label": "20-minute appointment", "price": 10, "available": True}],
        "info": {
            "suitable": [
                "You are considering treatment but want to ask questions first",
                "You have been declined elsewhere and want to understand why",
                "You want a second opinion on a treatment you are already using",
            ],
            "how": [
                "Book a slot at a time that suits you",
                "Join the video call at your appointment time",
                "Receive a written summary of what was discussed",
            ],
            "works": [
                "This is a conversation, not an assessment for supply. If you decide "
                "to go ahead afterwards you complete the full questionnaire and book "
                "a treatment consultation.",
            ],
            "other": [
                "Payment for this appointment is taken by SmartGP at the point of "
                "booking, because there is no product order for SmartRx to bill against.",
            ],
        },
        "cautions": ["I understand that no medicine will be prescribed or supplied from this appointment."],
        "module": ADVICE_MODULE,
        "approval": {"approved": True, "by": "Rachel Wood", "date": "2026-05-02"},
        "meta_title": "Advice-only weight loss consultation, no medicine | SmartGP",
        "meta_desc": "A 20-minute video appointment to talk through your weight loss "
                     "options with a UK-registered clinician. No medicine is prescribed "
                     "from this appointment.",
    },
    {
        "id": "mounjaro-tirzepatide",
        "kind": "injection",
        "name": "Mounjaro (tirzepatide)",
        "short": "Mounjaro",
        "inn": "tirzepatide",
        "strapline": "Weekly injection · dual GIP and GLP-1 action",
        "blurb": "A once-weekly injection licensed for weight management alongside "
                 "diet and exercise. The dose is increased in steps over several "
                 "months under clinical supervision.",
        "price_from": 149,
        "published": True,
        "strengths": [
            {"label": "2.5 mg", "price": 149, "available": True},
            {"label": "5 mg", "price": 165, "available": True},
            {"label": "7.5 mg", "price": 185, "available": True},
            {"label": "10 mg", "price": 205, "available": True},
            {"label": "12.5 mg", "price": 225, "available": False},
            {"label": "15 mg", "price": 245, "available": True},
        ],
        "info": {
            "suitable": [
                "Adults with a BMI of 30 or above",
                "Or a BMI of 27 to 29.9 with a weight-related health condition",
                "Not suitable if you are pregnant, breastfeeding or planning a pregnancy",
                "A clinician makes the final decision with you on the video call",
            ],
            "how": [
                "One injection each week, on the same day, into the stomach, thigh or upper arm",
                "A new pen is used for each dose",
                "Store in the fridge between 2\u00b0C and 8\u00b0C until first use",
            ],
            "works": [
                "Tirzepatide acts on two gut hormone receptors that regulate appetite "
                "and how full you feel after eating.",
                "It is used alongside a reduced-calorie diet and increased physical "
                "activity, not instead of them.",
            ],
            "other": [
                "Common side effects include nausea, diarrhoea, constipation and "
                "injection-site reactions, most often in the first weeks after a dose increase.",
                "Report any suspected side effect through the MHRA Yellow Card scheme.",
            ],
        },
        "cautions": [
            "I understand that treatment is used alongside changes to diet and activity, not instead of them.",
            "I understand the common side effects, including nausea and changes to bowel habit, and how to seek help.",
            "I understand that the dose is increased in steps and that I must not change the dose myself.",
            "I will read the patient information leaflet supplied with the medicine.",
        ],
        "module": GLP1_MODULE,
        "approval": {"approved": True, "by": "Rachel Wood", "date": "2026-05-14"},
        "meta_title": "Mounjaro (tirzepatide) | Prices and strengths | SmartGP",
        "meta_desc": "Mounjaro (tirzepatide) from \u00a3149 a month, including your video "
                     "appointment, medicine and delivery. All six strengths, prices and "
                     "side effects.",
    },
    {
        "id": "wegovy-semaglutide-injection",
        "kind": "injection",
        "name": "Wegovy (semaglutide injection)",
        "short": "Wegovy injection",
        "inn": "semaglutide",
        "strapline": "Weekly injection · GLP-1 receptor agonist",
        "blurb": "A once-weekly injection licensed for weight management alongside "
                 "diet and exercise, titrated over about 16 weeks to a maintenance dose.",
        "price_from": 139,
        "published": True,
        "strengths": [
            {"label": "0.25 mg", "price": 139, "available": True},
            {"label": "0.5 mg", "price": 149, "available": True},
            {"label": "1 mg", "price": 169, "available": True},
            {"label": "1.7 mg", "price": 189, "available": True},
            {"label": "2.4 mg", "price": 209, "available": True},
        ],
        "info": {
            "suitable": [
                "Adults with a BMI of 30 or above",
                "Or a BMI of 27 to 29.9 with a weight-related health condition",
                "Not suitable if you are pregnant, breastfeeding or planning a pregnancy",
            ],
            "how": [
                "One injection each week on the same day",
                "Rotate the injection site between the stomach, thigh and upper arm",
                "Keep refrigerated until first use",
            ],
            "works": [
                "Semaglutide mimics a gut hormone that signals fullness to the brain "
                "and slows stomach emptying.",
            ],
            "other": [
                "Nausea is the most commonly reported side effect and usually settles. "
                "Report suspected side effects via the Yellow Card scheme.",
            ],
        },
        "cautions": [
            "I understand that treatment is used alongside changes to diet and activity.",
            "I understand the common side effects and how to seek help if they are severe.",
            "I understand that stopping treatment often leads to weight being regained.",
            "I will read the patient information leaflet supplied with the medicine.",
        ],
        "module": GLP1_MODULE,
        "approval": {"approved": True, "by": "Rachel Wood", "date": "2026-05-14"},
        "meta_title": "Wegovy (semaglutide) | Prices and strengths | SmartGP",
        "meta_desc": "Wegovy (semaglutide) from \u00a3139 a month, including your video "
                     "appointment, medicine and delivery. All five strengths, prices and "
                     "side effects.",
    },
    {
        "id": "wegovy-oral-semaglutide",
        "kind": "oral",
        "name": "Wegovy (oral semaglutide)",
        "short": "Wegovy oral",
        "inn": "semaglutide",
        "strapline": "Daily tablet · no injection, no cold chain",
        "blurb": "A daily tablet form of semaglutide for people who would prefer not "
                 "to inject. Taken on an empty stomach with a small sip of water.",
        "price_from": 129,
        "published": True,
        "verify": True,
        "strengths": [
            {"label": "1.5 mg", "price": 129, "available": True},
            {"label": "4 mg", "price": 159, "available": True},
        ],
        "info": {
            "suitable": ["Adults who meet the BMI criteria and would prefer a tablet to an injection"],
            "how": [
                "One tablet each morning, at least 30 minutes before food, drink or other medicines",
                "Take with no more than half a glass of water",
            ],
            "works": ["The same active ingredient as the injection, formulated for absorption from the stomach."],
            "other": ["Timing matters more than with the injection — absorption drops sharply if taken with food."],
        },
        "cautions": [
            "I understand the tablet must be taken on an empty stomach for it to work.",
            "I understand the common side effects and how to seek help.",
            "I will read the patient information leaflet supplied with the medicine.",
        ],
        "module": GLP1_MODULE,
        "approval": {"approved": True, "by": "Rachel Wood", "date": "2026-05-14"},
        "meta_title": "Wegovy oral semaglutide tablet | Prices | SmartGP UK",
        "meta_desc": "A daily semaglutide tablet from \u00a3129 a month, including your "
                     "video appointment, medicine and delivery. How it works and who it suits.",
    },
    {
        "id": "orlistat-xenical",
        "kind": "oral",
        "name": "Orlistat (Xenical)",
        "short": "Orlistat",
        "inn": "orlistat",
        "strapline": "Capsule with meals · non-GLP-1 option",
        "blurb": "A capsule taken with meals that reduces the amount of fat absorbed "
                 "from food. A long-established option with a different exclusion "
                 "profile to the GLP-1 treatments.",
        "price_from": 39,
        "published": True,
        "strengths": [
            {"label": "120 mg — 84 capsules", "price": 39, "available": True},
            {"label": "120 mg — 252 capsules", "price": 99, "available": True},
        ],
        "info": {
            "suitable": [
                "Adults with a BMI of 30 or above, or 28 and above with a weight-related condition",
                "People who cannot take, or would rather not take, a GLP-1 treatment",
            ],
            "how": [
                "One capsule with each main meal containing fat, up to three times a day",
                "Skip the dose if a meal contains no fat",
            ],
            "works": [
                "Blocks an enzyme that breaks down dietary fat, so roughly a third of "
                "the fat you eat passes through undigested.",
            ],
            "other": [
                "Side effects relate directly to how much fat is eaten. A lower-fat "
                "diet reduces them considerably.",
            ],
        },
        "cautions": [
            "I understand that side effects are strongly linked to how much fat I eat.",
            "I understand a multivitamin may be recommended.",
            "I will read the patient information leaflet supplied with the medicine.",
        ],
        "module": ORLISTAT_MODULE,
        "approval": {"approved": True, "by": "Rachel Wood", "date": "2026-05-14"},
        "meta_title": "Orlistat (Xenical) | Prices and pack sizes | SmartGP",
        "meta_desc": "Orlistat (Xenical) from \u00a339, including your video appointment, "
                     "medicine and delivery. How it works, pack sizes and who it suits.",
    },
]

COMPARE = {
    "columns": ["Treatment", "Type", "How often", "Cold chain", "Who it suits"],
    "rows": [
        ["Mounjaro (tirzepatide)", "Injection", "Once weekly", "Yes",
         "BMI 30+, or 27–29.9 with a weight-related condition"],
        ["Wegovy (semaglutide)", "Injection", "Once weekly", "Yes",
         "BMI 30+, or 27–29.9 with a weight-related condition"],
        ["Wegovy oral", "Tablet", "Once daily", "No",
         "Same BMI criteria; prefer a tablet to an injection"],
        ["Orlistat (Xenical)", "Capsule", "With meals", "No",
         "BMI 30+, or 28+ with a condition; non-GLP-1 option"],
    ],
    "note": "A clinician confirms which treatment is right for you on your video "
            "call. This table compares treatment types, not prices. The price of "
            "every strength is on the pricing page.",
}

# ---------------------------------------------------------------------- FAQ
FAQS = [
    ("Before you book", "Do I have to have a video consultation?",
     "Yes. Weight loss medicines cannot be supplied on the basis of an online "
     "questionnaire alone, so every patient has a video appointment with a "
     "clinician before anything is prescribed. There is no route through this "
     "site that gets you a prescription without one."),
    ("Before you book", "What do I need to hand?",
     "A passport or UK driving licence, your GP practice details, and your height "
     "and weight. The questionnaire takes about eight minutes."),
    ("Before you book", "Will I definitely be prescribed treatment?",
     "No. The clinician decides at the appointment. If treatment is not right for "
     "you, you will not be charged and you will be told why, with advice on what "
     "to do next."),
    ("Before you book", "Can I choose which clinician I see?",
     "Not at the moment. Whichever clinician is available attends your appointment. "
     "You can see who they are on the meet the team page."),
    ("Cost and payment", "When do I pay?",
     "Not at booking. If the clinician approves treatment, SmartRx sends you a "
     "single payment link. The price you saw already includes the consultation fee."),
    ("Cost and payment", "Is there a subscription?",
     "No. Every supply is paid for on its own, and every supply follows a clinical review."),
    ("Cost and payment", "Can I cancel my appointment?",
     "Yes, from your dashboard. Because no payment is taken at booking there is no "
     "cancellation charge."),
    ("Your treatment", "How do I get a repeat supply?",
     "Request one from your dashboard. You complete a short check-in about your "
     "weight, dose and how you are getting on, then book a review appointment. "
     "Repeat supply is never automatic."),
    ("Your treatment", "How is my medicine delivered?",
     "SmartRx dispenses and delivers to your home address. Collection is not "
     "offered. Cold chain packaging is used for injections and an age check "
     "applies on delivery."),
    ("Your treatment", "How do I report a side effect?",
     "Use the side effect form in your dashboard so the clinic is alerted, and "
     "report it to the MHRA through the Yellow Card scheme."),
    ("Privacy and records", "Will you tell my GP?",
     "Only if you consent. We ask during the questionnaire and record your answer. "
     "You can be seen either way."),
    ("Privacy and records", "What happens to my ID document?",
     "It is held in encrypted storage that only clinical staff can open, and it is "
     "deleted 30 days after your identity has been confirmed."),
]

# ------------------------------------------------------------------- Learn
# Topic clusters. Each cluster has a hub page; every article links up to its
# hub, across to its siblings, and out to the treatment it concerns.
LEARN_CLUSTERS = [
    {
        "slug": "glp-1-medicines",
        "title": "GLP-1 medicines",
        "intro": "How this class of medicine works, what to expect month by month, "
                 "and what happens when treatment stops.",
        "meta_title": "GLP-1 medicines explained | Patient guides | SmartGP",
        "meta_desc": "Clinician-written guides to GLP-1 weight loss medicines: how "
                     "they work, why the dose is increased slowly, and what happens "
                     "when you stop.",
    },
    {
        "slug": "living-well",
        "title": "Eating and moving well",
        "intro": "Practical food and activity changes that work alongside treatment "
                 "rather than against it.",
        "meta_title": "Eating and moving well while on treatment | SmartGP",
        "meta_desc": "Protein, fibre and resistance training while losing weight. "
                     "Practical, clinician-reviewed guidance for people on weight "
                     "loss treatment.",
    },
    {
        "slug": "side-effects",
        "title": "Side effects",
        "intro": "What is common, what settles on its own, and what needs a clinician "
                 "the same day.",
        "meta_title": "Weight loss treatment side effects explained | SmartGP",
        "meta_desc": "Managing nausea and other common side effects of weight loss "
                     "treatment, and the symptoms that mean you should seek urgent help.",
    },
]

LEARN_ARTICLES = [
    {
        "slug": "how-glp-1-medicines-work",
        "cluster": "glp-1-medicines",
        "title": "How GLP-1 medicines work",
        "standfirst": "GLP-1 medicines copy a hormone your gut already makes after "
                      "eating. They slow your stomach down and turn appetite down — "
                      "which is why they work, and also why they can make you feel sick.",
        "author": "rachel-wood",
        "reviewer": "vinesh",
        "published": "2026-08-12",
        "updated": "2026-08-19",
        "next_review": "August 2027",
        "meta_title": "How GLP-1 medicines work for weight loss | SmartGP",
        "meta_desc": "How semaglutide and tirzepatide act on appetite and stomach "
                     "emptying, why Mounjaro targets two hormones, and why the dose "
                     "goes up slowly.",
        "related_treatments": ["mounjaro-tirzepatide", "wegovy-semaglutide-injection"],
        "sections": [
            ("what-glp-1-is", "What GLP-1 actually is", [
                "GLP-1 is a hormone your small intestine releases when you eat. It "
                "tells your pancreas to release insulin, tells your stomach to empty "
                "more slowly, and signals to the appetite centres in your brain that "
                "you have had enough. Your own GLP-1 breaks down within minutes.",
                "Semaglutide and tirzepatide are engineered versions that survive far "
                "longer — long enough that one injection covers a week.",
            ]),
            ("in-the-body", "What the medicine does in your body", [
                "Three things, all at once. Your stomach empties more slowly, so a "
                "meal keeps you full for longer. Your appetite signalling changes, so "
                "you want less food and think about it less. And your blood sugar "
                "response to eating improves.",
                "The appetite effect is the one people notice most. Many describe it "
                "as food noise going quiet rather than as being forced to eat less.",
            ]),
            ("two-hormones", "Why Mounjaro works on two hormones, not one", [
                "Wegovy acts on GLP-1 alone. Mounjaro acts on GLP-1 and a second gut "
                "hormone called GIP. In trials that combination produced more weight "
                "loss on average — though averages do not tell you what will happen "
                "for you specifically, and the treatment that suits you may not be "
                "the one with the bigger trial number.",
            ]),
            ("why-slow", "Why the dose goes up slowly", [
                "Almost all the sickness, stomach upset and fatigue people get from "
                "these medicines comes from going up in dose too fast. Starting low "
                "and increasing in steps of four weeks or more gives your gut time "
                "to adjust.",
                "This is why your clinician will not start you high even if you ask. "
                "It is also why a dose increase needs a proper appointment rather "
                "than a form — they need to know how you actually got on with the "
                "dose below it.",
            ]),
            ("month-by-month", "What to expect month by month", [
                "In the first month, on the starting dose, most people notice "
                "appetite changes within a week or two and some nausea, especially "
                "in the day or two after each injection. Weight change in month one "
                "is usually modest.",
                "From month two or three, as the dose steps up, weight loss typically "
                "becomes steadier. Side effects tend to flare briefly after each "
                "increase and then settle.",
                "Beyond that the pattern varies a lot between people. Your clinician "
                "reviews how it is going before each repeat, and adjusts rather than "
                "pushing on regardless.",
            ]),
        ],
        "refs": [
            "Electronic Medicines Compendium — Summary of Product Characteristics for tirzepatide and semaglutide. [link to be added before publication]",
            "National Institute for Health and Care Excellence — technology appraisal guidance on weight-management medicines. [link to be added before publication]",
            "Medicines and Healthcare products Regulatory Agency — Drug Safety Update on GLP-1 receptor agonists. [link to be added before publication]",
        ],
    },
    {
        "slug": "titration-explained",
        "cluster": "glp-1-medicines",
        "title": "Titration explained",
        "standfirst": "Titration is the planned, stepped increase in dose over months. "
                      "It is the single biggest factor in whether people tolerate "
                      "treatment well enough to stay on it.",
        "author": "rachel-wood",
        "reviewer": "vinesh",
        "published": "2026-08-05",
        "updated": "2026-08-19",
        "next_review": "August 2027",
        "meta_title": "Titration: why your dose goes up in steps | SmartGP",
        "meta_desc": "What titration means, how long each dose step lasts, what to "
                     "expect at each increase, and why a dose change always needs a "
                     "clinician.",
        "related_treatments": ["mounjaro-tirzepatide", "wegovy-semaglutide-injection"],
        "sections": [
            ("what-titration-is", "What titration means", [
                "Titration is simply raising a dose in planned steps rather than "
                "starting at the level you will end up on. With GLP-1 medicines the "
                "starting dose is deliberately too low to do much — its job is to let "
                "your gut get used to the medicine.",
            ]),
            ("how-long", "How long each step lasts", [
                "Usually four weeks, sometimes longer if you are still getting side "
                "effects. There is no prize for moving quickly, and moving up before "
                "you have settled is the most common reason people abandon treatment "
                "altogether.",
            ]),
            ("what-to-expect", "What to expect at each increase", [
                "A brief return of nausea or bowel changes in the few days after the "
                "step up, then a settling. If that does not settle, the answer is "
                "usually to hold at the current dose rather than push on.",
            ]),
            ("who-decides", "Who decides when you move up", [
                "Your clinician, at a review appointment, after asking how you got on "
                "with the dose below. A dose increase cannot be issued from a form, "
                "which is why every repeat request routes into a booking.",
            ]),
        ],
        "refs": [
            "Electronic Medicines Compendium — dose escalation schedules in the relevant Summaries of Product Characteristics. [link to be added before publication]",
        ],
    },
    {
        "slug": "when-you-stop-treatment",
        "cluster": "glp-1-medicines",
        "title": "What happens when you stop treatment",
        "standfirst": "Most people regain weight after stopping a GLP-1 medicine. "
                      "That is not a personal failure — it is what the evidence "
                      "predicts, and it is worth planning for before you start.",
        "author": "rachel-wood",
        "reviewer": "vinesh",
        "published": "2026-07-28",
        "updated": "2026-08-19",
        "next_review": "August 2027",
        "meta_title": "What happens when you stop weight loss treatment | SmartGP",
        "meta_desc": "Why weight is commonly regained after stopping a GLP-1 medicine, "
                     "how to plan for it, and how to come off treatment sensibly with "
                     "your clinician.",
        "related_treatments": ["mounjaro-tirzepatide", "wegovy-semaglutide-injection"],
        "sections": [
            ("what-happens", "What tends to happen", [
                "Appetite returns, often fairly quickly, and with it a good deal of "
                "the weight. Trial data consistently shows substantial regain in the "
                "year after stopping.",
            ]),
            ("why", "Why it happens", [
                "The medicine is treating an ongoing biological process, not curing "
                "it. When it is withdrawn, the appetite signalling it was altering "
                "goes back to how it was.",
            ]),
            ("planning", "Planning for it before you start", [
                "The habits built during treatment — the way you eat, the resistance "
                "training you keep up — are what carries over. Treatment buys you the "
                "conditions to build them; it does not build them for you.",
                "Talk to your clinician about what stopping looks like at your first "
                "appointment, not at your last.",
            ]),
        ],
        "refs": [
            "Published trial extension and withdrawal data for GLP-1 receptor agonists. [links to be added before publication]",
        ],
    },
    {
        "slug": "protein-fibre-and-feeling-full",
        "cluster": "living-well",
        "title": "Protein, fibre and feeling full",
        "standfirst": "When appetite drops sharply, the risk is not eating too much — "
                      "it is eating too little of the right things. Protein and fibre "
                      "are what to protect.",
        "author": "rachel-wood",
        "reviewer": "vinesh",
        "published": "2026-07-20",
        "updated": "2026-08-19",
        "next_review": "August 2027",
        "meta_title": "Protein and fibre while on weight loss treatment | SmartGP",
        "meta_desc": "Why appetite loss makes protein and fibre harder to get, and "
                     "practical ways to protect both while losing weight.",
        "related_treatments": ["mounjaro-tirzepatide"],
        "sections": [
            ("why-it-matters", "Why this matters more on treatment", [
                "If you are eating noticeably less overall, the composition of what "
                "you do eat matters more than it did before. Protein protects muscle; "
                "fibre keeps your bowels moving when a medicine is already slowing "
                "things down.",
            ]),
            ("practical", "Practical ways to protect both", [
                "Put the protein on the plate first and eat it first. Keep easy "
                "options that need no cooking for the days when you do not fancy "
                "anything. Drink more water than feels necessary.",
            ]),
            ("when-to-ask", "When to ask for help", [
                "If you are struggling to eat at all, or losing weight far faster "
                "than expected, tell your clinician rather than waiting for your next "
                "review.",
            ]),
        ],
        "refs": [
            "British Dietetic Association food fact sheets. [link to be added before publication]",
        ],
    },
    {
        "slug": "keeping-muscle-while-losing-weight",
        "cluster": "living-well",
        "title": "Keeping muscle while losing weight",
        "standfirst": "Rapid weight loss costs muscle as well as fat. Resistance "
                      "training is the part of this that most people skip and most "
                      "regret skipping.",
        "author": "rachel-wood",
        "reviewer": "vinesh",
        "published": "2026-07-14",
        "updated": "2026-08-19",
        "next_review": "August 2027",
        "meta_title": "Keeping muscle while you lose weight | SmartGP clinic",
        "meta_desc": "Why resistance training matters more than cardio during rapid "
                     "weight loss, and how much of it is actually needed.",
        "related_treatments": ["mounjaro-tirzepatide"],
        "sections": [
            ("the-problem", "What happens to muscle", [
                "Any substantial weight loss takes some lean mass with it. The faster "
                "the loss and the lower the protein intake, the larger that share tends to be.",
            ]),
            ("what-helps", "What actually helps", [
                "Resistance training two or three times a week, and enough protein. "
                "That is most of it. It does not need a gym membership or a "
                "complicated programme.",
            ]),
            ("getting-started", "Getting started without overdoing it", [
                "Start lighter than you think you need to and add gradually. The aim "
                "is something you will still be doing in six months.",
            ]),
        ],
        "refs": [
            "NHS physical activity guidelines for adults. [link to be added before publication]",
        ],
    },
    {
        "slug": "managing-nausea",
        "cluster": "side-effects",
        "title": "Managing nausea in the first month",
        "standfirst": "Nausea is the most common side effect of GLP-1 treatment and "
                      "usually the most short-lived. Here is what tends to help, and "
                      "the point at which it stops being normal.",
        "author": "rachel-wood",
        "reviewer": "vinesh",
        "published": "2026-07-08",
        "updated": "2026-08-19",
        "next_review": "August 2027",
        "meta_title": "Managing nausea on weight loss treatment | SmartGP",
        "meta_desc": "Why nausea happens in the first weeks of GLP-1 treatment, what "
                     "usually helps, and when to contact a clinician instead of waiting.",
        "related_treatments": ["mounjaro-tirzepatide", "wegovy-semaglutide-injection"],
        "sections": [
            ("why", "Why it happens", [
                "Your stomach is emptying more slowly than it used to. Food sits "
                "longer, and that feels like nausea, particularly in the day or two "
                "after a dose.",
            ]),
            ("what-helps", "What usually helps", [
                "Smaller meals, eaten more slowly. Less fat and less fried food. "
                "Stopping when you feel full rather than finishing the plate. Plenty "
                "of water through the day.",
            ]),
            ("when-to-call", "When to stop waiting and call", [
                "Severe or persistent vomiting, or severe abdominal pain that spreads "
                "to your back, is not ordinary nausea. Contact NHS 111, or 999 if it "
                "is severe, and tell us as well.",
            ]),
        ],
        "refs": [
            "MHRA Yellow Card scheme — reporting suspected adverse drug reactions. [link to be added before publication]",
        ],
    },
    {
        "slug": "when-to-seek-urgent-advice",
        "cluster": "side-effects",
        "title": "When to seek urgent advice",
        "standfirst": "Most side effects are a nuisance rather than a danger. A small "
                      "number are not. These are the ones that should not wait.",
        "author": "rachel-wood",
        "reviewer": "vinesh",
        "published": "2026-07-02",
        "updated": "2026-08-19",
        "next_review": "August 2027",
        "meta_title": "When to seek urgent advice during treatment | SmartGP",
        "meta_desc": "The symptoms that need urgent medical attention while on weight "
                     "loss treatment, and exactly where to go for them.",
        "related_treatments": ["mounjaro-tirzepatide", "wegovy-semaglutide-injection"],
        "sections": [
            ("call-999", "Call 999 for these", [
                "Swelling of the face, lips or tongue, or difficulty breathing. "
                "Collapse or loss of consciousness. Severe, sudden abdominal pain.",
            ]),
            ("call-111", "Call NHS 111 for these", [
                "Persistent vomiting you cannot keep fluids down against. Severe "
                "abdominal pain that spreads to your back. Signs of dehydration.",
            ]),
            ("tell-us", "Tell us as well", [
                "Use the side effect form in your account so a clinician sees it, and "
                "report it to the MHRA through the Yellow Card scheme. Reporting picks "
                "up problems that trials do not.",
            ]),
        ],
        "refs": [
            "NHS 111 service information. [link to be added before publication]",
        ],
    },
]

RESOURCES = [
    ("How to give your injection",
     "Step-by-step guidance on preparing the pen, choosing a site and rotating between sites."),
    ("Storage and cold chain",
     "Fridge temperatures, how long a pen lasts once out of the fridge, and what to do after a power cut."),
    ("Side effects and what to do",
     "What is common, what is not, and the symptoms that mean you should seek urgent help."),
    ("Diet and activity support",
     "Eating patterns, hydration and movement that support treatment."),
    ("Yellow Card reporting",
     "How to report a suspected side effect to the MHRA, and why it matters."),
    ("NHS weight management services",
     "What is available on the NHS and how to ask your GP about it."),
]

TESTIMONIALS = [
    ("The form told me exactly how long it would take and it was right. Booked a slot "
     "for the Tuesday and that was that.", "Patient, Leeds", "Booking experience"),
    ("I liked that nobody tried to sell me anything before the appointment. It felt "
     "like a clinic, not a shop.", "Patient, Bristol", "Consultation experience"),
    ("Delivery arrived cold and on the day I was told. The tracking link actually worked.",
     "Patient, Glasgow", "Delivery experience"),
]

CAREERS = [
    ("Independent Prescriber — weight management", "Remote (UK) · Sessional",
     "Conduct video consultations, prescribe within our clinical governance framework, "
     "and contribute to questionnaire content."),
    ("Pharmacy Dispenser", "SmartRx Pharmacy · Full time",
     "Dispensing, cold chain packing and dispatch for the SmartGP service."),
    ("Patient Support Coordinator", "Hybrid · Full time",
     "First line of contact for patients — bookings, delivery queries and escalation "
     "to the clinical team."),
]

LEGAL = {
    "terms": ("Terms and conditions", [
        ("Who we are", "SmartGP is a trading name of Smartway Pharma Limited. "
                       "Consultations are provided by UK-registered clinicians. Medicines "
                       "are dispensed and supplied by SmartRx Pharmacy."),
        ("What this service is", "A private, non-NHS service for UK residents aged 18 or "
                                 "over. Nothing on this site is a recommendation to take a particular "
                                 "medicine. All treatment decisions are made by a clinician during a "
                                 "video consultation."),
        ("Payment", "No payment is taken when you book. If treatment is approved, SmartRx "
                    "sends a payment link. The published price includes the consultation fee. "
                    "If you book an advice-only consultation, that fee is paid at the point "
                    "of booking."),
        ("Cancellation and refunds", "You may cancel or reschedule an appointment from your "
                                     "dashboard at any time before it starts, at no charge. Dispensed medicines "
                                     "are exempt from the 14-day distance-selling cancellation right for "
                                     "reasons of patient safety. Refunds are handled by SmartRx."),
        ("Delivery", "Medicines are delivered to your registered home address only. "
                     "Collection is not offered. An age check applies on delivery."),
        ("Your responsibilities", "You must answer the questionnaire honestly and "
                                  "completely, and the treatment must be for you alone. Supplying false "
                                  "information may put your health at risk and may result in the service "
                                  "being withdrawn."),
    ]),
    "privacy": ("Privacy policy", [
        ("What we collect", "Your identity and contact details, your address, your "
                            "questionnaire answers, your height and weight, your identity document, "
                            "and any weight verification evidence you provide."),
        ("Why we collect it", "To provide health care to you. Our lawful basis for "
                              "processing health data is the provision of health care by, or under the "
                              "responsibility of, a health professional. Where we rely on your consent — "
                              "for GP notification and for marketing — we record it separately and you "
                              "may withdraw it."),
        ("How long we keep it", "Questionnaire submissions and health data: 10 years. "
                                "Identity documents: deleted 30 days after verification. Verification "
                                "photographs: 10 years as evidence of safe supply. Booking records: 10 "
                                "years. Audit logs: 6 years minimum. Newsletter records: active "
                                "subscription plus 2 years."),
        ("Who sees it", "Clinical answers, identity documents and verification evidence "
                        "are visible only to clinical roles. Support and finance staff cannot see "
                        "them. Every access is logged."),
        ("Where it is held", "All data is hosted in the United Kingdom. No live patient "
                             "data is used in test environments."),
        ("Your rights", "You may request a copy of your data, ask for corrections, or ask "
                        "us to close your account. Clinical records we are required to keep are "
                        "retained for the statutory period."),
    ]),
    "cookies": ("Cookie policy", [
        ("Essential cookies", "Needed to keep you signed in and to keep the site secure. "
                              "These are always on and cannot be turned off."),
        ("Analytics cookies", "Help us understand which pages people use and where they "
                              "get stuck. Off until you accept. No health information is ever sent to "
                              "analytics."),
        ("Changing your mind", "You can withdraw consent at any time from this page. "
                               "Withdrawal takes effect immediately."),
    ]),
    "complaints": ("Complaints procedure", [
        ("Tell us first", "Email the clinic through the contact form or write to the "
                          "registered office. We acknowledge complaints within 3 working days and aim "
                          "to respond fully within 20 working days."),
        ("If you are not satisfied", "You may escalate to the General Pharmaceutical "
                                     "Council for matters relating to the pharmacy, or to the regulator of the "
                                     "prescribing clinician. Contact details are provided in our response."),
        ("Reporting a side effect", "A complaint is not the route for a suspected side "
                                    "effect. Use the side effect form in your account and the MHRA Yellow Card "
                                    "scheme."),
    ]),
    "accessibility": ("Accessibility statement", [
        ("Our commitment", "SmartGP aims to meet WCAG 2.2 AA across the public site, the "
                           "questionnaire, booking and your account."),
        ("What we have done", "Every form field has a visible label and an error message "
                              "that says what to fix. The whole journey works with a keyboard alone. "
                              "Motion is reduced if your device asks for it. Colour is never the only way "
                              "information is shown."),
        ("Problems", "If something on this site stops you doing what you came to do, tell "
                     "us through the contact form and we will fix it or give you another way to "
                     "complete the task."),
    ]),
}


def service(sid):
    for s in SERVICES:
        if s["id"] == sid:
            return s
    return None


def articles_in(cluster_slug):
    return [a for a in LEARN_ARTICLES if a["cluster"] == cluster_slug]


def person(slug):
    for p in TEAM:
        if p["slug"] == slug:
            return p
    return None


# ------------------------------------------------- common preliminary set
# Built once and attached to every service (BR-25).
COMMON = {
    "personal": [
        {"k": "title", "type": "select", "label": "Title",
         "options": ["Mr", "Mrs", "Miss", "Ms", "Mx", "Dr"], "required": True, "half": True},
        {"k": "firstName", "type": "text", "label": "First name", "required": True, "half": True},
        {"k": "lastName", "type": "text", "label": "Last name", "required": True, "half": True},
        {"k": "dob", "type": "date", "label": "Date of birth", "required": True, "half": True,
         "hint": "Must match your photo ID."},
        {"k": "sexAtBirth", "type": "radio", "label": "Sex registered at birth",
         "options": ["Female", "Male"], "required": True,
         "hint": "Asked because it determines whether pregnancy questions are shown. It is not a question about gender identity."},
        {"k": "mobile", "type": "tel", "label": "UK mobile number", "required": True,
         "half": True, "placeholder": "07700 900000",
         "hint": "Used for appointment confirmations and reminders."},
        {"k": "email", "type": "email", "label": "Email address", "required": True, "half": True},
        {"k": "postcode", "type": "postcode", "label": "UK postcode", "required": True},
        {"k": "address1", "type": "text", "label": "Address line 1", "required": True},
        {"k": "address2", "type": "text", "label": "Address line 2"},
        {"k": "town", "type": "text", "label": "Town or city", "required": True, "half": True},
        {"k": "county", "type": "text", "label": "County", "half": True},
    ],
    "gp": [
        {"k": "gpRegistered", "type": "radio",
         "label": "Are you registered with a UK GP practice?",
         "options": ["Yes", "No"], "required": True},
        {"k": "gpPractice", "type": "gplookup", "label": "Search for your practice",
         "showIf": {"k": "gpRegistered", "is": "Yes"}, "required": True},
        {"k": "gpConsent", "type": "radio",
         "label": "May the clinician send a summary of your consultation to your GP practice?",
         "options": ["Yes, I consent", "No, I do not consent"], "required": True,
         "showIf": {"k": "gpRegistered", "is": "Yes"},
         "hint": "Sharing keeps your medical record complete. You can say no and still be seen."},
        {"k": "anythingElse", "type": "textarea",
         "label": "Is there anything else you would like the clinician to know, or to ask them?",
         "placeholder": "Optional"},
    ],
    "consent": [
        {"k": "cTerms", "type": "consent", "required": True,
         "label": "I agree to the terms and conditions and the privacy policy."},
        {"k": "cPrivate", "type": "consent", "required": True,
         "label": "I understand this is a private service and that medication supplied here is not an NHS prescription."},
        {"k": "cFees", "type": "consent", "required": True,
         "label": "I understand that further tests or procedures, if recommended, may incur additional fees."},
        {"k": "cCancel", "type": "consent", "required": True,
         "label": "I have read and accept the cancellation policy."},
        {"k": "cAssess", "type": "consent", "required": True,
         "label": "I consent to a clinical assessment and to SmartGP processing my health information for that purpose."},
        {"k": "cMarketing", "type": "consent",
         "label": "Optional: send me recipes, service news and health information by email. You can unsubscribe at any time."},
    ],
    "conditions": [
        "Type 2 diabetes or pre-diabetes", "High blood pressure", "High cholesterol",
        "Obstructive sleep apnoea", "Osteoarthritis affecting weight-bearing joints",
        "Polycystic ovary syndrome", "Cardiovascular disease",
        "Non-alcoholic fatty liver disease", "None of these",
    ],
}

CHECKIN = [
    {"k": "currentWeight", "type": "number", "label": "Your current weight in kilograms",
     "required": True, "half": True},
    {"k": "currentDose", "type": "text", "label": "The dose you are currently taking",
     "required": True, "half": True},
    {"k": "tolerating", "type": "radio", "label": "How are you tolerating the treatment?",
     "options": ["Well — no real problems", "Some side effects but manageable",
                 "Struggling with side effects"], "required": True,
     "flag": {"when": ["Struggling with side effects"], "level": "caution",
              "note": "Tolerability problem reported"}},
    {"k": "sideEffects", "type": "textarea",
     "label": "Describe any side effects you have had since your last supply",
     "placeholder": "Or type \u201cnone\u201d", "required": True},
    {"k": "healthChange", "type": "radio",
     "label": "Has anything changed in your health, or in the medicines you take?",
     "options": ["No change", "Yes — something has changed"], "required": True,
     "flag": {"when": ["Yes — something has changed"], "level": "caution",
              "note": "Change in health or medication since last supply"}},
    {"k": "changeDetail", "type": "textarea", "label": "Tell us what has changed",
     "showIf": {"k": "healthChange", "is": "Yes — something has changed"}, "required": True},
    {"k": "pregnancyNow", "type": "radio",
     "label": "Are you pregnant, breastfeeding, or planning a pregnancy?",
     "options": ["None of these", "Yes"], "required": True,
     "showIf": {"k": "sexAtBirth", "is": "Female"},
     "flag": {"when": ["Yes"], "level": "exclusion",
              "note": "Treatment must stop — urgent clinician review"}},
]

BOOKING = {
    "timezone": "Europe/London",
    "durationMins": 20, "bufferMins": 5, "leadTimeHours": 24,
    "horizonDays": 21, "maxPerDay": 14,
    "workingDays": [1, 2, 3, 4, 5], "hours": {"from": 9, "to": 18},
    "closures": ["2026-08-31"],
    "clinicians": ["Rachel Wood", "Vinesh"],
}
