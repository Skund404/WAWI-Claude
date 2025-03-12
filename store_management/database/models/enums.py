# database/models/enums.py
"""
Comprehensive Enumeration classes for the leatherworking store management system.

This module defines all enum types used throughout the application,
covering various aspects of the business from sales to project management.
"""

import enum
from enum import Enum, auto
from typing import Dict, Any, List


# Sales and Order Management Enums
class SaleStatus(Enum):
    """Detailed enumeration of sale statuses for custom leatherwork."""
    # Initial contact and consultation
    INQUIRY = "inquiry"
    QUOTE_REQUEST = "quote_request"
    DESIGN_CONSULTATION = "design_consultation"

    # Design and approval phase
    DESIGN_PROPOSAL = "design_proposal"
    DESIGN_APPROVAL = "design_approval"

    # Production preparation
    MATERIALS_SOURCING = "materials_sourcing"
    PATTERN_CREATION = "pattern_creation"
    DEPOSIT_RECEIVED = "deposit_received"

    # Production phase
    IN_PRODUCTION = "in_production"
    CUTTING = "cutting"
    ASSEMBLY = "assembly"
    STITCHING = "stitching"
    FINISHING = "finishing"
    HARDWARE_INSTALLATION = "hardware_installation"
    QUALITY_REVIEW = "quality_review"

    # Delivery phase
    READY_FOR_PICKUP = "ready_for_pickup"
    FINAL_PAYMENT_PENDING = "final_payment_pending"
    FINAL_PAYMENT_RECEIVED = "final_payment_received"
    SHIPPED = "shipped"
    DELIVERED = "delivered"

    # Completion and follow-up
    COMPLETED = "completed"
    FEEDBACK_REQUESTED = "feedback_requested"
    REVIEW_RECEIVED = "review_received"

    # Issue handling
    REVISION_REQUESTED = "revision_requested"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

    # Legacy statuses for backward compatibility
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"


# Alias for SaleStatus to maintain compatibility with existing code
SalesStatus = SaleStatus


class PaymentStatus(Enum):
    """Payment status for orders and transactions."""
    PENDING = "pending"
    DEPOSIT_PENDING = "deposit_pending"
    DEPOSIT_PAID = "deposit_paid"
    BALANCE_PENDING = "balance_pending"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    PAYMENT_PLAN = "payment_plan"
    INSTALLMENT_DUE = "installment_due"
    OVERDUE = "overdue"
    REFUND_REQUESTED = "refund_requested"
    PARTIALLY_REFUNDED = "partially_refunded"
    REFUNDED = "refunded"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"
    GIFT_CERTIFICATE = "gift_certificate"
    STORE_CREDIT = "store_credit"


class PurchaseStatus(Enum):
    """Status values for purchase orders from suppliers."""
    PLANNING = "planning"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SUBMITTED_TO_SUPPLIER = "submitted_to_supplier"
    ACKNOWLEDGED = "acknowledged"
    BACKORDERED = "backordered"
    PROCESSING = "processing"
    PARTIAL_SHIPMENT = "partial_shipment"
    SHIPPED = "shipped"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    QUALITY_INSPECTION = "quality_inspection"
    PAYMENT_PENDING = "payment_pending"
    COMPLETE = "complete"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"

    # Legacy statuses for backward compatibility
    DRAFT = "draft"
    ORDERED = "ordered"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"


# Customer-related Enums
class CustomerStatus(Enum):
    """Represents the current status of a customer in the system."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"
    POTENTIAL = "potential"
    FIRST_PURCHASE = "first_purchase"
    RETURNING = "returning"
    REPEAT = "repeat"
    WHOLESALE = "wholesale"
    DEALER = "dealer"
    EDUCATIONAL = "educational"

    # Legacy statuses for backward compatibility
    BLOCKED = "blocked"
    LEAD = "lead"


class CustomerTier(Enum):
    """Represents different customer loyalty or spending tiers."""
    NEW = "new"
    STANDARD = "standard"
    PREMIUM = "premium"
    VIP = "vip"
    ARTISAN = "artisan"
    CRAFTSMAN = "craftsman"
    MASTER_CRAFTSMAN = "master_craftsman"
    WHOLESALE_BASIC = "wholesale_basic"
    WHOLESALE_PREMIUM = "wholesale_premium"
    DEALER = "dealer"
    TRADE = "trade"
    EDUCATIONAL = "educational"
    INDUSTRY_PARTNER = "industry_partner"

    # Legacy tiers for backward compatibility
    WHOLESALE = "wholesale"


class CustomerSource(Enum):
    """Represents the source or channel through which the customer was acquired."""
    WEBSITE = "website"
    ONLINE_STORE = "online_store"
    MARKETPLACE = "marketplace"
    RETAIL = "retail"
    REFERRAL = "referral"
    PROFESSIONAL_REFERRAL = "professional_referral"
    MARKETING = "marketing"
    SOCIAL_MEDIA = "social_media"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    PINTEREST = "pinterest"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    TRADE_SHOW = "trade_show"
    CRAFT_FAIR = "craft_fair"
    WORKSHOP = "workshop"
    GUILD = "guild"
    CONVENTION = "convention"
    WORD_OF_MOUTH = "word_of_mouth"
    EMAIL_CAMPAIGN = "email_campaign"
    BLOG = "blog"
    MAGAZINE = "magazine"
    BOOK = "book"
    NEWSPAPER = "newspaper"
    DIRECT_MAIL = "direct_mail"
    SEARCH_ENGINE = "search_engine"
    PARTNERSHIP = "partnership"
    OTHER = "other"

    # Legacy sources for backward compatibility
    EXHIBITION = "exhibition"
    DIRECT = "direct"


# Inventory and Material Management Enums
class InventoryStatus(Enum):
    """Enumeration of inventory status values."""
    IN_STOCK = "in_stock"
    ABUNDANT = "abundant"
    SUFFICIENT = "sufficient"
    LOW_STOCK = "low_stock"
    CRITICALLY_LOW = "critically_low"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"
    ON_ORDER = "on_order"
    BACKORDERED = "backordered"
    PRE_ORDER = "pre_order"
    AVAILABLE = "available"
    RESERVED = "reserved"
    ALLOCATED = "allocated"
    DAMAGED = "damaged"
    DEFECTIVE = "defective"
    PENDING_INSPECTION = "pending_inspection"
    PENDING_ARRIVAL = "pending_arrival"
    RECEIVING = "receiving"
    QUARANTINE = "quarantine"
    SEASONAL = "seasonal"
    LIMITED_EDITION = "limited_edition"
    SPECIAL_ORDER = "special_order"
    CUSTOM_ORDER = "custom_order"


class MaterialType(Enum):
    """Comprehensive material types for leatherworking."""
    # Thread and stitching materials
    THREAD = 'thread'
    WAXED_THREAD = 'waxed_thread'
    LINEN_THREAD = 'linen_thread'
    NYLON_THREAD = 'nylon_thread'
    POLYESTER_THREAD = 'polyester_thread'

    # Leather materials
    LEATHER = "leather"
    VEGAN_LEATHER = "vegan_leather"
    SYNTHETIC_LEATHER = "synthetic_leather"

    # Linings and backing materials
    LINING = "lining"
    BACKING = "backing"
    INTERFACING = "interfacing"
    STABILIZER = "stabilizer"
    BATTING = "batting"

    # Adhesives and fastening
    ADHESIVE = "adhesive"
    CONTACT_CEMENT = "contact_cement"
    GLUE = "glue"
    TAPE = "tape"

    # Edge finishing and treatment
    DYE = "dye"
    FINISH = "finish"
    EDGE_PAINT = "edge_paint"
    EDGE_COAT = "edge_coat"
    WAX = "wax"
    BURNISHING_GUM = "burnishing_gum"
    SEALER = "sealer"

    # Hardware components
    HARDWARE = "hardware"
    RIVETS = "rivets"
    BUCKLES = "buckles"
    ZIPPERS = "zippers"
    SNAPS = "snaps"
    BUTTONS = "buttons"
    HOOKS = "hooks"
    RINGS = "rings"
    CLASPS = "clasps"

    # Structural components
    ELASTIC = "elastic"
    WEBBING = "webbing"
    STRAPPING = "strapping"
    PIPING = "piping"
    CORD = "cord"
    DRAWSTRING = "drawstring"

    # Internal components
    PADDING = "padding"
    FOAM = "foam"
    FILLER = "filler"
    STIFFENER = "stiffener"
    REINFORCEMENT = "reinforcement"

    # Miscellaneous
    PATTERN_PAPER = "pattern_paper"
    TRANSFER_PAPER = "transfer_paper"
    TEMPLATE_MATERIAL = "template_material"
    MARKING_TOOL = "marking_tool"
    CLEANING_PRODUCT = "cleaning_product"
    CONDITIONING_PRODUCT = "conditioning_product"
    PACKAGING = "packaging"
    OTHER = "other"

    # Legacy types for backward compatibility
    SUPPLIES = "supplies"


class MaterialQualityGrade(Enum):
    """Quality grades for leather and other materials."""
    PREMIUM = 'premium'
    PROFESSIONAL = 'professional'
    STANDARD = 'standard'
    ECONOMY = 'economy'
    SECONDS = 'seconds'
    REMNANT = 'remnant'
    SCRAP = 'scrap'
    SAMPLE = 'sample'
    PROTOTYPE = 'prototype'
    RECLAIMED = 'reclaimed'
    SUSTAINABLE = 'sustainable'
    ARTISAN = 'artisan'
    HANDCRAFTED = 'handcrafted'
    VINTAGE = 'vintage'
    FACTORY_REJECT = 'factory_reject'
    CLEARANCE = 'clearance'


# Hardware-related Enums
class HardwareType(Enum):
    """Types of hardware used in leatherworking projects."""
    # Buckles and fasteners
    BUCKLE = "buckle"
    ROLLER_BUCKLE = "roller_buckle"
    CENTER_BAR_BUCKLE = "center_bar_buckle"
    HEEL_BAR_BUCKLE = "heel_bar_buckle"
    DOUBLE_BAR_BUCKLE = "double_bar_buckle"
    HALTER_BUCKLE = "halter_buckle"
    CONWAY_BUCKLE = "conway_buckle"  # Fixed typo from Conway_BUCKLE
    QUICK_RELEASE_BUCKLE = "quick_release_buckle"
    THREE_BAR_SLIDE = "three_bar_slide"
    SLOTTED_BUCKLE = "slotted_buckle"
    LOCKING_BUCKLE = "locking_buckle"

    # Snaps and closures
    SNAP = "snap"
    LINE_20_SNAP = "line_20_snap"
    LINE_24_SNAP = "line_24_snap"
    MAGNETIC_SNAP = "magnetic_snap"
    SPRING_SNAP = "spring_snap"
    BALL_SNAP = "ball_snap"
    HEAVY_DUTY_SNAP = "heavy_duty_snap"

    # Rivets and attachment hardware
    RIVET = "rivet"
    RAPID_RIVET = "rapid_rivet"
    COPPER_RIVET = "copper_rivet"
    DOUBLE_CAP_RIVET = "double_cap_rivet"
    TUBULAR_RIVET = "tubular_rivet"
    SPLIT_RIVET = "split_rivet"
    DECORATIVE_RIVET = "decorative_rivet"
    SPIKE_RIVET = "spike_rivet"
    STUD_RIVET = "stud_rivet"

    # Zippers
    ZIPPER = "zipper"
    METAL_ZIPPER = "metal_zipper"
    NYLON_ZIPPER = "nylon_zipper"
    INVISIBLE_ZIPPER = "invisible_zipper"
    WATERPROOF_ZIPPER = "waterproof_zipper"
    TWO_WAY_ZIPPER = "two_way_zipper"
    SEPARATING_ZIPPER = "separating_zipper"
    CONTINUOUS_ZIPPER = "continuous_zipper"
    LOCKING_ZIPPER = "locking_zipper"

    # Connector hardware
    CLASP = "clasp"
    LOBSTER_CLASP = "lobster_clasp"
    TRIGGER_SNAP = "trigger_snap"
    TRIGGER_HOOK = "trigger_hook"
    SWIVEL_HOOK = "swivel_hook"
    SWIVEL_EYE_BOLT = "swivel_eye_bolt"
    SWIVEL_EYE_SNAP = "swivel_eye_snap"

    # Buttons and toggles
    BUTTON = "button"
    JEANS_BUTTON = "jeans_button"
    TOGGLE = "toggle"
    TOGGLE_CLOSURE = "toggle_closure"

    # Rings
    D_RING = "d_ring"
    O_RING = "o_ring"
    TRIANGLE_RING = "triangle_ring"
    SQUARE_RING = "square_ring"
    RECTANGLE_RING = "rectangle_ring"
    HALF_RING = "half_ring"
    OVAL_RING = "oval_ring"
    WELDED_RING = "welded_ring"
    CAST_RING = "cast_ring"
    SOLID_RING = "solid_ring"
    HEAVY_DUTY_RING = "heavy_duty_ring"

    # Closures
    MAGNETIC_CLOSURE = "magnetic_closure"
    TWIST_LOCK = "twist_lock"
    TURNLOCK = "turnlock"
    FLIP_LOCK = "flip_lock"
    TONGUE_LOCK = "tongue_lock"
    KISS_LOCK = "kiss_lock"
    PUSH_LOCK = "push_lock"
    BOX_LOCK = "box_lock"
    HASP = "hasp"
    LATCH = "latch"

    # Specialty hardware
    CARABINER = "carabiner"
    LOCKING_CARABINER = "locking_carabiner"
    QUICK_LINK = "quick_link"
    BOLT_SNAP = "bolt_snap"
    SHACKLE = "shackle"
    PARACHUTE_CLIP = "parachute_clip"
    TENSION_LOCK = "tension_lock"

    # Adjustable hardware
    ROLLER = "roller"
    SLIDER = "slider"
    ADJUSTER = "adjuster"
    STRAP_ADJUSTER = "strap_adjuster"
    LADDER_LOCK = "ladder_lock"
    STRAP_KEEPER = "strap_keeper"
    STRAP_LOOP = "strap_loop"
    STRAP_TIP = "strap_tip"

    # Adult product specific hardware
    LOCKING_CONNECTOR = "locking_connector"
    QUICK_RELEASE_CONNECTOR = "quick_release_connector"
    ROTATING_CONNECTOR = "rotating_connector"
    SAFETY_RELEASE = "safety_release"
    MULTI_WAY_CONNECTOR = "multi_way_connector"
    EMERGENCY_RELEASE = "emergency_release"

    # Decorative hardware
    SPIKE = "spike"
    CONICAL_SPIKE = "conical_spike"
    DOME_STUD = "dome_stud"
    PYRAMID_STUD = "pyramid_stud"
    CONCHO = "concho"
    DECORATIVE_CONCHO = "decorative_concho"
    NAILHEAD = "nailhead"
    HAMMERED_STUD = "hammered_stud"

    # Miscellaneous hardware
    KEY_RING = "key_ring"
    KEY_FOBS = "key_fobs"
    EYELET = "eyelet"
    GROMMET = "grommet"
    HOOK = "hook"
    STUD = "stud"
    SAM_BROWNE_STUD = "sam_browne_stud"
    SCREW = "screw"
    CHICAGO_SCREW = "chicago_screw"
    LOCK = "lock"
    PADLOCK = "padlock"
    CHAIN = "chain"
    PLATE = "plate"
    CORNER = "corner"
    CORNER_PROTECTOR = "corner_protector"
    PURSE_FEET = "purse_feet"
    BAG_BOTTOM = "bag_bottom"
    TASSEL_CAP = "tassel_cap"
    CORD_END = "cord_end"
    OTHER = "other"


class HardwareMaterial(Enum):
    """Materials that hardware items can be made of."""
    # Metals
    BRASS = "brass"
    ANTIQUE_BRASS = "antique_brass"
    STEEL = "steel"
    STAINLESS_STEEL = "stainless_steel"
    NICKEL = "nickel"
    NICKEL_FREE = "nickel_free"
    SILVER = "silver"
    STERLING_SILVER = "sterling_silver"
    SILVER_PLATE = "silver_plate"
    GOLD = "gold"
    GOLD_PLATE = "gold_plate"
    ROSE_GOLD = "rose_gold"
    BRONZE = "bronze"
    GUNMETAL = "gunmetal"
    ANTIQUE_METAL = "antique_metal"
    ALUMINUM = "aluminum"
    COPPER = "copper"
    ZINC = "zinc"
    PEWTER = "pewter"
    TITANIUM = "titanium"
    CHROME = "chrome"

    # Non-metals
    PLASTIC = "plastic"
    ACRYLIC = "acrylic"
    NYLON = "nylon"
    RESIN = "resin"
    HORN = "horn"
    BONE = "bone"
    MOTHER_OF_PEARL = "mother_of_pearl"
    SHELL = "shell"
    CARBON_FIBER = "carbon_fiber"
    WOOD = "wood"
    BAMBOO = "bamboo"
    CERAMIC = "ceramic"
    GLASS = "glass"
    LEATHER_WRAPPED = "leather_wrapped"
    FABRIC_WRAPPED = "fabric_wrapped"
    STONE = "stone"
    OTHER = "other"


class HardwareFinish(Enum):
    """Finishes that can be applied to hardware items."""
    POLISHED = "polished"
    MIRROR_POLISHED = "mirror_polished"
    BRUSHED = "brushed"
    ANTIQUE = "antique"
    MATTE = "matte"
    SATIN = "satin"
    CHROME = "chrome"
    NICKEL_PLATED = "nickel_plated"
    BRASS_PLATED = "brass_plated"
    GOLD_PLATED = "gold_plated"
    SILVER_PLATED = "silver_plated"
    COPPER_PLATED = "copper_plated"
    BLACK_OXIDE = "black_oxide"
    PAINTED = "painted"
    POWDER_COATED = "powder_coated"
    ENAMELED = "enameled"
    LACQUERED = "lacquered"
    NATURAL = "natural"
    DISTRESSED = "distressed"
    HAMMERED = "hammered"
    EMBOSSED = "embossed"
    ENGRAVED = "engraved"
    PATINA = "patina"
    AGED = "aged"
    WEATHERED = "weathered"
    GALVANIZED = "galvanized"
    ANODIZED = "anodized"
    ELECTROPLATED = "electroplated"
    BURNISHED = "burnished"
    BLACKENED = "blackened"
    TEXTURED = "textured"
    RUSTIC = "rustic"
    VINTAGE = "vintage"
    MILITARY_SPEC = "military_spec"
    HYPOALLERGENIC = "hypoallergenic"
    OTHER = "other"


# Leather-related Enums
class LeatherType(Enum):
    """Extensive enumeration of leather types and characteristics."""
    # Tanning Methods
    VEGETABLE_TANNED = "vegetable_tanned"
    CHROME_TANNED = "chrome_tanned"
    BRAIN_TANNED = "brain_tanned"
    ALUM_TANNED = "alum_tanned"
    OIL_TANNED = "oil_tanned"
    COMBINATION_TANNED = "combination_tanned"
    BARK_TANNED = "bark_tanned"
    FORMALDEHYDE_TANNED = "formaldehyde_tanned"
    SMOKE_TANNED = "smoke_tanned"

    # Leather Grades
    FULL_GRAIN = "full_grain"
    TOP_GRAIN = "top_grain"
    CORRECTED_GRAIN = "corrected_grain"
    SPLIT = "split"
    GENUINE_LEATHER = "genuine_leather"
    BONDED_LEATHER = "bonded_leather"

    # Specialty Leathers
    NUBUCK = "nubuck"
    SUEDE = "suede"
    PATENT_LEATHER = "patent_leather"
    SHELL_CORDOVAN = "shell_cordovan"
    LATIGO = "latigo"
    CHAMOIS = "chamois"
    TOOLING_LEATHER = "tooling_leather"
    SKIRTING_LEATHER = "skirting_leather"
    HARNESS_LEATHER = "harness_leather"
    BRIDLE_LEATHER = "bridle_leather"
    UPHOLSTERY_LEATHER = "upholstery_leather"
    GARMENT_LEATHER = "garment_leather"
    LINING_LEATHER = "lining_leather"
    EMBOSSED_LEATHER = "embossed_leather"
    HAIR_ON_HIDE = "hair_on_hide"
    EXOTIC = "exotic"

    # Animal Sources - Traditional
    COWHIDE = "cowhide"
    CALFSKIN = "calfskin"
    GOATSKIN = "goatskin"
    KIDSKIN = "kidskin"
    SHEEPSKIN = "sheepskin"
    LAMBSKIN = "lambskin"
    DEERSKIN = "deerskin"
    PIGSKIN = "pigskin"
    HORSE = "horse"
    BUFFALO = "buffalo"
    BISON = "bison"
    ELK = "elk"
    MOOSE = "moose"
    KANGAROO = "kangaroo"

    # Animal Sources - Exotic
    ALLIGATOR = "alligator"
    CROCODILE = "crocodile"
    SNAKE = "snake"
    PYTHON = "python"
    LIZARD = "lizard"
    OSTRICH = "ostrich"
    STINGRAY = "stingray"
    SHARK = "shark"
    ELEPHANT = "elephant"
    FROG = "frog"

    # Alternative and Sustainable Options
    SYNTHETIC = "synthetic"
    VEGAN = "vegan"
    RECYCLED = "recycled"
    MUSHROOM_LEATHER = "mushroom_leather"
    CORK_LEATHER = "cork_leather"
    PLANT_BASED = "plant_based"
    PINEAPPLE_LEATHER = "pineapple_leather"
    APPLE_LEATHER = "apple_leather"
    CACTUS_LEATHER = "cactus_leather"
    PAPER_LEATHER = "paper_leather"
    WASHABLE_LEATHER = "washable_leather"
    LAB_GROWN = "lab_grown"
    OCEAN_PLASTIC = "ocean_plastic"


class LeatherFinish(Enum):
    """Detailed enumeration of leather finishing techniques."""
    ANILINE = "aniline"
    SEMI_ANILINE = "semi_aniline"
    PIGMENTED = "pigmented"
    ANTIQUED = "antiqued"
    HAND_RUBBED = "hand_rubbed"
    WAX_PULL_UP = "wax_pull_up"
    OIL_PULL_UP = "oil_pull_up"
    BURNISHED = "burnished"
    DISTRESSED = "distressed"
    DRUM_DYED = "drum_dyed"
    HAND_DYED = "hand_dyed"
    HAND_STAINED = "hand_stained"
    PATENT = "patent"
    NAPPA = "nappa"
    TUMBLED = "tumbled"
    PEBBLED = "pebbled"
    EMBOSSED = "embossed"
    PRINTED = "printed"
    GLAZED = "glazed"
    MATTE = "matte"
    OILED = "oiled"
    WAXED = "waxed"
    NATURAL = "natural"
    POLISHED = "polished"
    SUEDED = "sueded"
    NUBUCKED = "nubucked"
    BRUSHED = "brushed"
    CRACKLED = "crackled"
    METALLIC = "metallic"
    PEARLIZED = "pearlized"
    IRIDESCENT = "iridescent"
    WATERPROOF = "waterproof"
    RUSTIC = "rustic"
    STONE_WASHED = "stone_washed"
    HAND_FINISHED = "hand_finished"
    MATTE_FINISH = "matte_finish"
    GLOSSY_FINISH = "glossy_finish"

    # Specialty finishes
    TOOLED = "tooled"
    CARVED = "carved"
    STAMPED = "stamped"
    HEAT_STAMPED = "heat_stamped"
    BASKET_WEAVE = "basket_weave"
    FLORAL_TOOLED = "floral_tooled"
    GEOMETRIC_TOOLED = "geometric_tooled"
    CUSTOM_TOOLED = "custom_tooled"

    # Additional finishes
    HAND_BUFFED = "hand_buffed"
    TEXTURED = "textured"
    SMOOTH = "smooth"
    PERFORATED = "perforated"
    LASER_ETCHED = "laser_etched"
    APPLIQUED = "appliqued"
    AIRBRUSHED = "airbrushed"
    STUDDED = "studded"
    SPIKED = "spiked"
    RIVETED = "riveted"

    # Treatment-focused finishes
    BICAST = "bicast"
    LATIGO = "latigo"
    TWO_TONE = "two_tone"
    OMBRE = "ombre"
    PAINTED = "painted"
    HEAT_TREATED = "heat_treated"
    SEALED = "sealed"
    CONDITIONED = "conditioned"

    # Specialty adult product finishes
    WATER_RESISTANT = "water_resistant"
    BODY_SAFE = "body_safe"
    HYPOALLERGENIC = "hypoallergenic"
    MOISTURE_RESISTANT = "moisture_resistant"
    EASY_CLEAN = "easy_clean"
    SANITIZABLE = "sanitizable"
    REINFORCED = "reinforced"
    PADDED = "padded"
    LINED = "lined"
    DOUBLE_LAYERED = "double_layered"


# Product and Project Management Enums
class ProjectType(Enum):
    """Comprehensive enumeration of leatherworking project types."""
    # Small leather goods
    WALLET = "wallet"
    BIFOLD_WALLET = "bifold_wallet"
    TRIFOLD_WALLET = "trifold_wallet"
    LONG_WALLET = "long_wallet"
    CARD_HOLDER = "card_holder"
    MONEY_CLIP = "money_clip"
    CARD_WALLET = "card_wallet"
    COIN_PURSE = "coin_purse"
    PASSPORT_HOLDER = "passport_holder"
    ID_HOLDER = "id_holder"
    BADGE_HOLDER = "badge_holder"
    KEY_CASE = "key_case"
    KEY_FOBS = "key_fobs"
    LUGGAGE_TAG = "luggage_tag"

    # Bags and cases
    BRIEFCASE = "briefcase"
    ATTACHE_CASE = "attache_case"
    MESSENGER_BAG = "messenger_bag"
    TOTE_BAG = "tote_bag"
    HANDBAG = "handbag"
    PURSE = "purse"
    CLUTCH = "clutch"
    BACKPACK = "backpack"
    DUFFLE_BAG = "duffle_bag"
    WEEKENDER_BAG = "weekender_bag"
    LAPTOP_BAG = "laptop_bag"
    LAPTOP_SLEEVE = "laptop_sleeve"
    TABLET_CASE = "tablet_case"
    PHONE_CASE = "phone_case"
    CAMERA_BAG = "camera_bag"
    COSMETIC_BAG = "cosmetic_bag"
    TOILETRY_BAG = "toiletry_bag"
    SATCHEL = "satchel"
    SADDLE_BAG = "saddle_bag"
    SHOULDER_BAG = "shoulder_bag"
    BUCKET_BAG = "bucket_bag"

    # Wearables
    BELT = "belt"
    DRESS_BELT = "dress_belt"
    CASUAL_BELT = "casual_belt"
    WORK_BELT = "work_belt"
    WESTERN_BELT = "western_belt"
    WATCH_STRAP = "watch_strap"
    WATCH_BAND = "watch_band"
    BRACELET = "bracelet"
    CUFF = "cuff"
    WRISTBAND = "wristband"
    COLLAR = "collar"
    HARNESS = "harness"
    SUSPENDERS = "suspenders"
    HOLSTER = "holster"
    SHOULDER_HOLSTER = "shoulder_holster"
    KNIFE_SHEATH = "knife_sheath"
    AXE_SHEATH = "axe_sheath"
    TOOL_SHEATH = "tool_sheath"

    # Accessories
    NOTEBOOK_COVER = "notebook_cover"
    JOURNAL_COVER = "journal_cover"
    BOOK_COVER = "book_cover"
    PLANNER_COVER = "planner_cover"
    CAMERA_STRAP = "camera_strap"
    GUITAR_STRAP = "guitar_strap"
    DOG_COLLAR = "dog_collar"
    DOG_LEASH = "dog_leash"
    TOOL_ROLL = "tool_roll"
    TOOL_POUCH = "tool_pouch"
    EYEGLASS_CASE = "eyeglass_case"
    KNIFE_ROLL = "knife_roll"
    VALET_TRAY = "valet_tray"
    COASTER = "coaster"
    MOUSE_PAD = "mouse_pad"
    DESK_MAT = "desk_mat"
    BOOKMARK = "bookmark"

    # Home and decor
    HOME_DECOR = "home_decor"
    FURNITURE = "furniture"
    UPHOLSTERY = "upholstery"
    WALL_HANGING = "wall_hanging"
    PILLOW = "pillow"
    LAMPSHADE = "lampshade"
    DRAWER_PULL = "drawer_pull"
    PICTURE_FRAME = "picture_frame"

    # BDSM and Adult Products
    ADULT_PRODUCTS = "adult_products"
    FETISH_WEAR = "fetish_wear"
    BDSM_GEAR = "bdsm_gear"
    FETISH_COLLAR = "fetish_collar"
    FETISH_CUFF = "fetish_cuff"
    WRIST_RESTRAINT = "wrist_restraint"
    ANKLE_RESTRAINT = "ankle_restraint"
    RESTRAINT_SET = "restraint_set"
    HARNESS_ADULT = "harness_adult"
    BODY_HARNESS = "body_harness"
    CHEST_HARNESS = "chest_harness"
    LEG_HARNESS = "leg_harness"
    COLLAR_ADULT = "collar_adult"
    POSTURE_COLLAR = "posture_collar"
    LEASH_ADULT = "leash_adult"
    PADDLE = "paddle"
    FLOGGER = "flogger"
    WHIP = "whip"
    CROP = "crop"
    MASK = "mask"
    BLINDFOLD = "blindfold"
    GAG = "gag"
    HOOD = "hood"
    COSTUME = "costume"
    ACCESSORY_ADULT = "accessory_adult"

    # Cosplay and Costume
    COSPLAY = "cosplay"
    COSTUME_PIECE = "costume_piece"
    ARMOR = "armor"
    BRACER = "bracer"
    PAULDRON = "pauldron"
    GREAVE = "greave"
    COSTUME_MASK = "costume_mask"
    PROP = "prop"
    BELT_COSTUME = "belt_costume"
    HOLSTER_COSTUME = "holster_costume"

    # Specialized categories
    CUSTOM = "custom"
    REPAIR = "repair"
    RESTORATION = "restoration"
    COMMISSION = "commission"
    BESPOKE = "bespoke"
    PROTOTYPE = "prototype"
    SAMPLE = "sample"
    PRODUCTION = "production"

    # Other
    OTHER = "other"


class ProjectStatus(Enum):
    """Detailed project status for custom leatherwork."""
    # Planning phase
    CONCEPT = "concept"
    PLANNING = "planning"
    INITIAL_CONSULTATION = "initial_consultation"
    DESIGN_PHASE = "design_phase"
    DESIGN_RESEARCH = "design_research"
    REFERENCE_GATHERING = "reference_gathering"
    SKETCH_PHASE = "sketch_phase"
    PATTERN_DEVELOPMENT = "pattern_development"
    PATTERN_TESTING = "pattern_testing"
    CLIENT_APPROVAL = "client_approval"

    # Preparation phase
    MATERIAL_SELECTION = "material_selection"
    MATERIAL_SAMPLING = "material_sampling"
    MATERIAL_PURCHASED = "material_purchased"
    MATERIAL_PREPARATION = "material_preparation"
    TOOL_PREPARATION = "tool_preparation"

    # Production phase
    PRODUCTION_QUEUE = "production_queue"
    CUTTING = "cutting"
    SKIVING = "skiving"
    PREPARATION = "preparation"
    DYEING = "dyeing"
    ASSEMBLY = "assembly"
    GLUING = "gluing"
    STITCHING = "stitching"
    HOLE_PUNCHING = "hole_punching"
    EDGE_FINISHING = "edge_finishing"
    BEVELING = "beveling"
    BURNISHING = "burnishing"
    PAINTING = "painting"
    HARDWARE_INSTALLATION = "hardware_installation"
    EMBOSSING = "embossing"
    TOOLING = "tooling"
    STAMPING = "stamping"
    CONDITIONING = "conditioning"
    POLISHING = "polishing"

    # Finishing phase
    QUALITY_CHECK = "quality_check"
    REVISIONS = "revisions"
    FINAL_TOUCHES = "final_touches"
    PHOTOGRAPHY = "photography"
    DOCUMENTATION = "documentation"
    PACKAGING = "packaging"

    # Delivery phase
    READY_FOR_DELIVERY = "ready_for_delivery"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    COMPLETED = "completed"

    # Other statuses
    ON_HOLD = "on_hold"
    DELAYED = "delayed"
    WAITING_FOR_MATERIALS = "waiting_for_materials"
    WAITING_FOR_TOOLS = "waiting_for_tools"
    WAITING_FOR_CLIENT = "waiting_for_client"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    CANCELLED = "cancelled"

    # Legacy statuses for backward compatibility
    PLANNED = "planned"
    MATERIALS_READY = "materials_ready"
    IN_PROGRESS = "in_progress"


class SkillLevel(Enum):
    """Skill levels for leatherworking techniques and projects."""
    ABSOLUTE_BEGINNER = "absolute_beginner"
    NOVICE = "novice"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    MASTER = "master"
    PROFESSIONAL = "professional"
    SPECIALIST = "specialist"
    ARTISAN = "artisan"
    APPRENTICE = "apprentice"
    JOURNEYMAN = "journeyman"
    MASTER_CRAFTSMAN = "master_craftsman"
    INSTRUCTOR = "instructor"


# Component-related Enums
class ComponentType(Enum):
    """Enumeration of component types used in patterns and projects."""
    # Structural and base components
    LEATHER = auto()
    HARDWARE = auto()
    THREAD = auto()
    LINING = auto()
    REINFORCEMENT = auto()

    # Pattern components
    TEMPLATE = auto()
    PATTERN_PIECE = auto()
    CUTOUT = auto()
    PANEL = auto()
    GUSSET = auto()

    # Functional components
    FASTENER = auto()
    EDGE_FINISH = auto()
    STRAP = auto()
    HANDLE = auto()
    SHOULDER_STRAP = auto()
    CROSSBODY_STRAP = auto()
    WRIST_STRAP = auto()
    POCKET = auto()
    ZIPPERED_POCKET = auto()
    SLIP_POCKET = auto()
    FLAP = auto()
    DIVIDER = auto()
    CLOSURE = auto()

    # Decorative components
    EMBELLISHMENT = auto()
    LOGO = auto()
    MONOGRAM = auto()
    APPLIQUE = auto()
    INLAY = auto()
    OVERLAY = auto()
    TRIM = auto()
    PIPING = auto()
    EDGING = auto()
    STUDS = auto()
    SPIKES = auto()
    RIVETS_DECORATIVE = auto()
    CONCHOS = auto()

    # Specialized components
    PADDING = auto()
    FOAM_INSERT = auto()
    STIFFENER = auto()
    REINFORCEMENT_STRIP = auto()
    BINDING = auto()
    CORNER_PIECE = auto()
    EDGE_BINDING = auto()
    WELT = auto()
    PLEAT = auto()
    DART = auto()

    # Adult and specialty components
    RESTRAINT_COMPONENT = auto()
    CONNECTOR_RING = auto()
    CONNECTOR_LOOP = auto()
    PADDING_PROTECTIVE = auto()
    LINING_SOFT = auto()
    LINING_SMOOTH = auto()
    QUICK_RELEASE = auto()
    SAFETY_COMPONENT = auto()
    ATTACHMENT_POINT = auto()
    REINFORCED_STRESS_POINT = auto()
    LOCKING_MECHANISM = auto()
    ADJUSTABLE_STRAP = auto()

    # Cosplay and costume components
    ARMOR_PLATE = auto()
    ARMOR_SECTION = auto()
    ARTICULATION_JOINT = auto()
    COSTUME_DETAIL = auto()
    ORNAMENTAL_PIECE = auto()
    WEATHERING_ELEMENT = auto()

    # Catch-all for unique or custom components
    OTHER = auto()


# Tool-related Enums
class ToolCategory(enum.Enum):
    """Categorization of leatherworking tools."""
    # Cutting tools
    CUTTING = "CUTTING"
    KNIFE = "KNIFE"
    SCISSOR = "SCISSOR"
    SHEARS = "SHEARS"
    ROTARY_CUTTER = "ROTARY_CUTTER"
    LASER_CUTTER = "LASER_CUTTER"

    # Hole making and punching
    PUNCHING = "PUNCHING"
    HOLE_PUNCH = "HOLE_PUNCH"
    STITCHING_PUNCH = "STITCHING_PUNCH"
    PRICKING_IRON = "PRICKING_IRON"
    DIAMOND_CHISEL = "DIAMOND_CHISEL"
    OBLONG_PUNCH = "OBLONG_PUNCH"
    ROUND_PUNCH = "ROUND_PUNCH"
    STRAP_END_PUNCH = "STRAP_END_PUNCH"

    # Stitching tools
    STITCHING = "STITCHING"
    NEEDLE = "NEEDLE"
    AWL = "AWL"
    STITCHING_GROOVER = "STITCHING_GROOVER"
    STITCHING_WHEEL = "STITCHING_WHEEL"
    THREAD_CONDITIONER = "THREAD_CONDITIONER"
    THIMBLE = "THIMBLE"
    PALM_GUARD = "PALM_GUARD"

    # Measuring and marking
    MEASURING = "MEASURING"
    RULER = "RULER"
    SQUARE = "SQUARE"
    DIVIDER = "DIVIDER"
    WING_DIVIDER = "WING_DIVIDER"
    COMPASS = "COMPASS"
    MARKING_TOOL = "MARKING_TOOL"
    TEMPLATE = "TEMPLATE"
    STITCH_MARKER = "STITCH_MARKER"

    # Finishing tools
    FINISHING = "FINISHING"
    BURNISHER = "BURNISHER"
    SLICKER = "SLICKER"
    GLAZING_TOOL = "GLAZING_TOOL"
    POLISHING_TOOL = "POLISHING_TOOL"

    # Edge work tools
    EDGE_WORK = "EDGE_WORK"
    EDGE_BEVELER = "EDGE_BEVELER"
    EDGE_CREASER = "EDGE_CREASER"
    FILETEUSE = "FILETEUSE"
    EDGE_PAINTER = "EDGE_PAINTER"

    # Dyeing and finishing chemicals
    DYEING = "DYEING"
    DYE_APPLICATOR = "DYE_APPLICATOR"
    SPONGE = "SPONGE"
    DAUBER = "DAUBER"
    BRUSH = "BRUSH"
    AIRBRUSH = "AIRBRUSH"

    # Surface treatment
    CONDITIONING = "CONDITIONING"
    APPLICATOR = "APPLICATOR"
    BUFFING_CLOTH = "BUFFING_CLOTH"
    POLISHING_CLOTH = "POLISHING_CLOTH"

    # Installation tools
    HARDWARE_INSTALLATION = "HARDWARE_INSTALLATION"
    SETTING_TOOL = "SETTING_TOOL"
    RIVET_SETTER = "RIVET_SETTER"
    SNAP_SETTER = "SNAP_SETTER"
    GROMMET_SETTER = "GROMMET_SETTER"
    EYELET_SETTER = "EYELET_SETTER"
    SETTER_DIE = "SETTER_DIE"
    ANVIL = "ANVIL"
    MALLET = "MALLET"
    HAMMER = "HAMMER"
    PRESS = "PRESS"

    # Pattern and design tools
    PATTERN_MAKING = "PATTERN_MAKING"
    DRAFTING_TOOL = "DRAFTING_TOOL"
    TRACING_TOOL = "TRACING_TOOL"
    FRENCH_CURVE = "FRENCH_CURVE"
    CIRCLE_TEMPLATE = "CIRCLE_TEMPLATE"

    # Specialized leather craft tools
    LEATHER_CRAFT = "LEATHER_CRAFT"
    STAMPING_TOOL = "STAMPING_TOOL"
    SWIVEL_KNIFE = "SWIVEL_KNIFE"
    MODELING_TOOL = "MODELING_TOOL"
    EMBOSSING_TOOL = "EMBOSSING_TOOL"
    SKIVER = "SKIVER"
    CREASER = "CREASER"

    # Work holding tools
    WORK_HOLDING = "WORK_HOLDING"
    STITCHING_PONY = "STITCHING_PONY"
    STITCHING_HORSE = "STITCHING_HORSE"
    CLAMP = "CLAMP"
    VISE = "VISE"
    MAGNIFIER = "MAGNIFIER"

    # Machine tools
    MACHINE = "MACHINE"
    SEWING_MACHINE = "SEWING_MACHINE"
    SPLITTER = "SPLITTER"
    BELL_SKIVER = "BELL_SKIVER"
    ELECTRIC_CREASER = "ELECTRIC_CREASER"
    THICKNESS_GAUGE = "THICKNESS_GAUGE"
    HEAT_TOOL = "HEAT_TOOL"


# For backward compatibility - ToolCategory is used in uppercase in some places and lowercase in others
ToolType = Enum('ToolType', [
    ('cutting', 'cutting'),
    ('punching', 'punching'),
    ('stitching', 'stitching'),
    ('edge_finishing', 'edge_finishing'),
    ('stamping', 'stamping'),
    ('measurement', 'measurement'),
    ('assembly', 'assembly'),
    ('dyeing', 'dyeing'),
    ('finishing', 'finishing'),
    ('pattern_making', 'pattern_making'),
    ('hardware', 'hardware'),
    ('work_holding', 'work_holding'),
    ('machine', 'machine'),
    ('other', 'other')
])


# Edge Finishing Enums
class EdgeFinishType(Enum):
    """Comprehensive edge finishing techniques for leatherwork."""
    BURNISHED = "burnished"
    SLICKED = "slicked"
    PAINTED = "painted"
    EDGE_KOTED = "edge_koted"
    EDGE_PAINTED = "edge_painted"
    RAW = "raw"
    NATURAL = "natural"
    BEVELED = "beveled"
    ROUNDED = "rounded"
    FOLDED = "folded"
    BOUND = "bound"
    STITCHED = "stitched"
    SEALED = "sealed"
    POLISHED = "polished"
    ROUGH = "rough"
    WAXED = "waxed"
    GLAZED = "glazed"
    DYED = "dyed"
    STAINED = "stained"
    GLOSSY = "glossy"
    MATTE = "matte"
    SATIN = "satin"
    OILED = "oiled"
    ANTIQUE = "antique"
    DISTRESSED = "distressed"
    CREASED = "creased"
    ROLLED = "rolled"
    PIPED = "piped"
    TRIMMED = "trimmed"
    BRAIDED = "braided"
    WRAPPED = "wrapped"
    FRENCH_EDGE = "french_edge"
    TURNED_EDGE = "turned_edge"
    DOUBLE_FOLDED = "double_folded"
    SKIVED_EDGE = "skived_edge"
    HOT_CREASED = "hot_creased"
    RECESSED = "recessed"


# Transaction and Inventory Management Enums
class TransactionType(Enum):
    """Enumeration of transaction types."""
    PURCHASE = "purchase"
    SALE = "sale"
    WHOLESALE_PURCHASE = "wholesale_purchase"
    WHOLESALE_SALE = "wholesale_sale"
    CONSIGNMENT_IN = "consignment_in"
    CONSIGNMENT_OUT = "consignment_out"
    SAMPLE_IN = "sample_in"
    SAMPLE_OUT = "sample_out"
    USAGE = "usage"
    PRODUCTION_USAGE = "production_usage"
    PROJECT_USAGE = "project_usage"
    SAMPLE_USAGE = "sample_usage"
    WASTAGE = "wastage"
    TRAINING_USAGE = "training_usage"
    ADJUSTMENT = "adjustment"
    INVENTORY_CORRECTION = "inventory_correction"
    LOSS = "loss"
    THEFT = "theft"
    DAMAGE = "damage"
    EXPIRATION = "expiration"
    RETURN = "return"
    CUSTOMER_RETURN = "customer_return"
    SUPPLIER_RETURN = "supplier_return"
    WASTE = "waste"
    TRANSFER = "transfer"
    LOCATION_TRANSFER = "location_transfer"
    REVERSAL = "reversal"
    DONATION = "donation"
    GIFT = "gift"
    WARRANTY_REPLACEMENT = "warranty_replacement"
    CONVERSION = "conversion"
    SWAP = "swap"
    LOAN_OUT = "loan_out"
    LOAN_RETURN = "loan_return"
    DEFECT_ANALYSIS = "defect_analysis"
    PROMOTIONAL = "promotional"
    EXHIBITION = "exhibition"
    PHOTOGRAPHY = "photography"
    MARKDOWN = "markdown"
    INTERNAL_USE = "internal_use"


class InventoryAdjustmentType(Enum):
    """Types of inventory adjustments."""
    INITIAL_STOCK = "initial_stock"
    RESTOCK = "restock"
    REORDER = "reorder"
    EMERGENCY_REORDER = "emergency_reorder"
    BULK_PURCHASE = "bulk_purchase"
    USAGE = "usage"
    DAMAGE = "damage"
    DEFECT = "defect"
    QUALITY_ISSUE = "quality_issue"
    LOST = "lost"
    THEFT = "theft"
    FOUND = "found"
    MISCOUNTED = "miscounted"
    EXPIRED = "expired"
    RETURN = "return"
    SUPPLIER_ERROR = "supplier_error"
    SUPPLIER_SHORTAGE = "supplier_shortage"
    SUPPLIER_EXCESS = "supplier_excess"
    INCORRECT_SHIPMENT = "incorrect_shipment"
    INCORRECT_RECORDING = "incorrect_recording"
    DATA_ENTRY_ERROR = "data_entry_error"
    SYSTEM_ERROR = "system_error"
    PHYSICAL_COUNT = "physical_count"
    CYCLE_COUNT = "cycle_count"
    ANNUAL_INVENTORY = "annual_inventory"
    CONVERSION = "conversion"
    RECLASSIFICATION = "reclassification"
    OBSOLETE = "obsolete"
    DISCONTINUED = "discontinued"
    WRITE_OFF = "write_off"
    SHRINKAGE = "shrinkage"


# Supplier-related Enums
class SupplierStatus(Enum):
    """Enumeration of supplier status values."""
    ACTIVE = "active"
    PREFERRED = "preferred"
    STRATEGIC = "strategic"
    PRIMARY = "primary"
    SECONDARY = "secondary"
    BACKUP = "backup"
    OCCASIONAL = "occasional"
    NEW = "new"
    PROBATIONARY = "probationary"
    INACTIVE = "inactive"
    PENDING = "pending"
    PENDING_APPROVAL = "pending_approval"
    PENDING_REVIEW = "pending_review"
    UNDER_EVALUATION = "under_evaluation"
    APPROVED = "approved"
    QUALIFIED = "qualified"
    BLACKLISTED = "blacklisted"
    BANNED = "banned"
    DISPUTED = "disputed"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    # Legacy statuses for backward compatibility
    ON_HOLD = "on_hold"


# Storage-related Enums
class StorageLocationType(Enum):
    """Enumeration of storage location types."""
    SHELF = "shelf"
    BIN = "bin"
    DRAWER = "drawer"
    CABINET = "cabinet"
    RACK = "rack"
    BOX = "box"
    PALLET = "pallet"
    CONTAINER = "container"
    BASKET = "basket"
    TRAY = "tray"
    TOTE = "tote"
    ROLL = "roll"
    HANGER = "hanger"
    FOLDER = "folder"
    FILING_CABINET = "filing_cabinet"
    CUBBY = "cubby"
    HOOK = "hook"
    PEGBOARD = "pegboard"
    SAFE = "safe"
    VAULT = "vault"
    REFRIGERATOR = "refrigerator"
    FREEZER = "freezer"
    CLIMATE_CONTROLLED = "climate_controlled"
    WAREHOUSE = "warehouse"
    STOCKROOM = "stockroom"
    WORKSHOP = "workshop"
    RETAIL_FLOOR = "retail_floor"
    DISPLAY_CASE = "display_case"
    SHOWROOM = "showroom"
    STUDIO = "studio"
    VEHICLE = "vehicle"
    OFFSITE = "offsite"
    STORAGE_UNIT = "storage_unit"
    OTHER = "other"


# Measurement and Quality Enums
class MeasurementUnit(Enum):
    """Enumeration of measurement units."""
    # Count-based
    PIECE = "piece"
    PAIR = "pair"
    SET = "set"
    UNIT = "unit"
    PACK = "pack"
    BOX = "box"
    ROLL = "roll"
    SPOOL = "spool"
    COIL = "coil"
    BUNDLE = "bundle"

    # Length-based
    MILLIMETER = "millimeter"
    CENTIMETER = "centimeter"
    METER = "meter"
    INCH = "inch"
    INCHES = "inches"
    FOOT = "foot"
    FEET = "feet"
    YARD = "yard"

    # Area-based
    SQUARE_MILLIMETER = "square_millimeter"
    SQUARE_CENTIMETER = "square_centimeter"
    SQUARE_METER = "square_meter"
    SQUARE_INCH = "square_inch"
    SQUARE_FOOT = "square_foot"
    SQUARE_YARD = "square_yard"
    HIDE = "hide"
    HALF_HIDE = "half_hide"
    SHOULDER = "shoulder"
    BELLY = "belly"
    BEND = "bend"

    # Weight-based
    MILLIGRAM = "milligram"
    GRAM = "gram"
    KILOGRAM = "kilogram"
    OUNCE = "ounce"
    POUND = "pound"

    # Volume-based
    MILLILITER = "milliliter"
    LITER = "liter"
    FLUID_OUNCE = "fluid_ounce"
    CUP = "cup"
    PINT = "pint"
    QUART = "quart"
    GALLON = "gallon"

    # Thickness
    MILLIMETER_THICKNESS = "millimeter_thickness"
    OUNCE_WEIGHT = "ounce_weight"  # Leather thickness in ounces
    IRONS = "irons"  # Traditional leather thickness

    # Other specialized
    LINE = "line"  # For buttons, snaps
    GAUGE = "gauge"  # For wire, needles
    STITCH_COUNT = "stitch_count"
    TEETH_PER_INCH = "teeth_per_inch"  # For zippers

    # Other
    OTHER = "other"


class QualityGrade(Enum):
    """Detailed quality grading for leatherwork."""
    MUSEUM_QUALITY = "museum_quality"
    HEIRLOOM = "heirloom"
    EXHIBITION = "exhibition"
    PREMIUM = "premium"
    PROFESSIONAL = "professional"
    ARTISAN = "artisan"
    STANDARD = "standard"
    COMMERCIAL = "commercial"
    WORKSHOP = "workshop"
    STUDENT = "student"
    PROTOTYPE = "prototype"
    SAMPLE = "sample"
    PRACTICE = "practice"
    EXPERIMENTAL = "experimental"
    CUSTOM = "custom"
    BESPOKE = "bespoke"
    HANDMADE = "handmade"
    MACHINE_MADE = "machine_made"
    FACTORY = "factory"

    # Legacy grades for backward compatibility
    ECONOMY = "economy"
    SECONDS = "seconds"
    DAMAGED = "damaged"


class PickingListStatus(Enum):
    """
    Enumeration of picking list status values.
    Represents the current state of a picking list in the workflow.
    """
    DRAFT = "draft"
    PENDING = "pending"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ASSIGNED = "assigned"
    PRIORITIZED = "prioritized"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    PICKING = "picking"
    PARTIALLY_PICKED = "partially_picked"
    PICKED = "picked"
    PACKING = "packing"
    PACKED = "packed"
    QUALITY_CHECK = "quality_check"
    AWAITING_MATERIALS = "awaiting_materials"
    BACK_ORDER = "back_order"
    HOLD = "hold"
    RELEASED = "released"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"
    ARCHIVED = "archived"


class ToolListStatus(Enum):
    """
    Enumeration of tool list status values.
    Represents the current state of a tool list in the workflow.
    """
    DRAFT = "draft"
    PENDING = "pending"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ASSIGNED = "assigned"
    GATHERING = "gathering"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    IN_USE = "in_use"
    ACTIVE = "active"
    MAINTENANCE_DUE = "maintenance_due"
    MAINTENANCE_IN_PROGRESS = "maintenance_in_progress"
    MISSING_TOOLS = "missing_tools"
    DAMAGED_TOOLS = "damaged_tools"
    AWAITING_REPLACEMENTS = "awaiting_replacements"
    RETURNING = "returning"
    RETURNED = "returned"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"
    ARCHIVED = "archived"


# Customer Communication Enums
class CommunicationChannel(Enum):
    """Channels through which customer communications occur."""
    EMAIL = "email"
    PHONE = "phone"
    TEXT_MESSAGE = "text_message"
    WEBSITE = "website"
    CHAT = "chat"
    VIDEO_CALL = "video_call"
    IN_PERSON = "in_person"
    SOCIAL_MEDIA = "social_media"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    MESSENGER = "messenger"
    WHATSAPP = "whatsapp"
    POSTAL_MAIL = "postal_mail"
    TRADE_SHOW = "trade_show"
    MARKETPLACE = "marketplace"
    OTHER = "other"


class CommunicationType(Enum):
    """Types of customer communications."""
    INQUIRY = "inquiry"
    QUOTE_REQUEST = "quote_request"
    ORDER_CONFIRMATION = "order_confirmation"
    SHIPPING_NOTIFICATION = "shipping_notification"
    DELIVERY_CONFIRMATION = "delivery_confirmation"
    STATUS_UPDATE = "status_update"
    FEEDBACK_REQUEST = "feedback_request"
    CUSTOMER_FEEDBACK = "customer_feedback"
    COMPLAINT = "complaint"
    RETURN_REQUEST = "return_request"
    WARRANTY_CLAIM = "warranty_claim"
    REPAIR_REQUEST = "repair_request"
    PAYMENT_REMINDER = "payment_reminder"
    MARKETING = "marketing"
    NEWSLETTER = "newsletter"
    PROMOTION = "promotion"
    FOLLOW_UP = "follow_up"
    THANK_YOU = "thank_you"
    DESIGN_CONSULTATION = "design_consultation"
    CARE_INSTRUCTIONS = "care_instructions"
    PRODUCT_INFORMATION = "product_information"
    OTHER = "other"