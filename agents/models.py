"""
================================================================================
                        WEB3.AI - DATABASE MODELS MODULE
================================================================================
YEH FILE DATABASE MODELS DEFINE KARTI HAI (Django ORM)

MODELS IN THIS FILE:
1. AnalysisTransaction - AI agent ka har ek use store karta hai

DATABASE: SQLite (Development) / PostgreSQL (Production)

LOCATION: agents/models.py

YEH DATA STORE HOTA HAI:
- User ne konsa agent use kiya
- Kya input diya (URL/Audio file)
- Kya output mila (AI response)
- Payment details (tx hash, cost)
- Timestamp

RELATIONSHIPS:
┌─────────────────────────────────────────────────────────────────────┐
│  WalletUser (wallet app)  ←──┐                                     │
│       ↑                       │                                     │
│       │ ForeignKey            │                                     │
│       │                       │                                     │
│  AnalysisTransaction ─────────┘                                     │
│       │                                                             │
│       └── Stores: input, output, payment, timestamp                 │
└─────────────────────────────────────────────────────────────────────┘
================================================================================
"""

# ============================================================================
# IMPORTS
# ============================================================================

from django.db import models        # Django ORM - Database models ke liye
from django.conf import settings    # Django settings (AUTH_USER_MODEL)


# ============================================================================
# ANALYSIS TRANSACTION MODEL
# ============================================================================

class AnalysisTransaction(models.Model):
    """
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║  ANALYSIS TRANSACTION MODEL                                               ║
    ║  Har AI agent usage ka record store karta hai                            ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    
    YEH MODEL KYA STORE KARTA HAI:
    - User: Kisne use kiya (WalletUser reference)
    - Category: Konsa agent category (GITHUB/AUDIO/COMPETESCAN)
    - Agent Type: Specific task (summary, pr_review, meeting_notes)
    - Input: User ne kya diya (URL, text, audio file)
    - Output: AI ne kya return kiya (JSON format mein)
    - Payment: Transaction hash aur cost
    - Timestamp: Kab use hua
    
    USAGE EXAMPLE:
    ```python
    # Naya transaction create karo
    txn = AnalysisTransaction.objects.create(
        user=request.user,
        category='GITHUB',
        agent_type='summary',
        input_text='https://github.com/user/repo',
        output_data='{"summary": "..."}',
        tx_hash='0x1234...',
        cost=0.0002
    )
    
    # User ke transactions fetch karo
    transactions = AnalysisTransaction.objects.filter(user=request.user)
    ```
    
    DATABASE TABLE: agents_analysistransaction
    """
    
    # ┌──────────────────────────────────────────────────────────────────────────┐
    # │ AGENT CATEGORIES - Konse types ke agents available hain                  │
    # └──────────────────────────────────────────────────────────────────────────┘
    # Yeh choices dropdown mein dikhenge admin panel mein
    AGENT_CATEGORIES = [
        ('GITHUB', 'GitHub Agent'),        # Code repository analysis
        ('AUDIO', 'Audio Agent'),          # Meeting transcription
        ('COMPETESCAN', 'CompeteScan AI'), # Competitor analysis
        ('SCRAPER', 'Web Scraper'),        # x402 Scraper (NEW)
    ]
    
    # ┌──────────────────────────────────────────────────────────────────────────┐
    # │ USER FIELD - Konse user ne agent use kiya                                │
    # │ ForeignKey = One-to-Many relationship (User can have many transactions) │
    # └──────────────────────────────────────────────────────────────────────────┘
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,           # WalletUser model reference
        on_delete=models.CASCADE,           # User delete = Transactions bhi delete
        related_name='analyses'             # user.analyses.all() se access karo
    )
    
    # ┌──────────────────────────────────────────────────────────────────────────┐
    # │ CATEGORY & AGENT TYPE - Kaunsa agent aur task type                       │
    # └──────────────────────────────────────────────────────────────────────────┘
    category = models.CharField(
        max_length=20, 
        choices=AGENT_CATEGORIES            # Dropdown options
    )  # e.g., 'GITHUB', 'AUDIO', 'COMPETESCAN'
    
    agent_type = models.CharField(
        max_length=50
    )  # e.g., 'summary', 'pr_review', 'meeting_assistant', 'competitor_analysis'
    
    # ┌──────────────────────────────────────────────────────────────────────────┐
    # │ INPUT FIELDS - User ne kya input diya                                    │
    # └──────────────────────────────────────────────────────────────────────────┘
    
    title = models.CharField(
        max_length=255, 
        blank=True, 
        null=True
    )  # Display name - Audio file name ya Repo name
    
    input_text = models.TextField(
        blank=True, 
        null=True
    )  # Text input - GitHub URL ya Website URL
    
    input_file = models.FileField(
        upload_to='uploads/audio/',         # Files yahan save hongi: media/uploads/audio/
        blank=True, 
        null=True
    )  # File input - Audio files ke liye
    
    # ┌──────────────────────────────────────────────────────────────────────────┐
    # │ OUTPUT FIELD - AI ne kya response diya                                   │
    # │ JSON format mein store hota hai as text                                  │
    # │ Example: {"summary": "...", "todos": [...], "deadlines": [...]}         │
    # └──────────────────────────────────────────────────────────────────────────┘
    output_data = models.TextField(
        blank=True, 
        null=True
    )  # AI response as JSON string
    
    # ┌──────────────────────────────────────────────────────────────────────────┐
    # │ PAYMENT FIELDS - Transaction details                                     │
    # │ x402 Protocol: tx_hash = x-payment header value                          │
    # └──────────────────────────────────────────────────────────────────────────┘
    
    tx_hash = models.CharField(
        max_length=100,                     # Blockchain tx hash (0x...) - 66 chars
        blank=True, 
        null=True
    )  # Transaction hash - Payment proof
    
    cost = models.DecimalField(
        max_digits=20,                      # Total 20 digits
        decimal_places=18,                  # 18 decimal places (ETH/MON standard)
        default=0.001                       # Default cost
    )  # Amount in MON (e.g., 0.0001, 0.0005, 0.0011)
    
    # ┌──────────────────────────────────────────────────────────────────────────┐
    # │ TIMESTAMP - Kab create hua                                               │
    # └──────────────────────────────────────────────────────────────────────────┘
    created_at = models.DateTimeField(
        auto_now_add=True                   # Automatically set on creation
    )

    # ┌──────────────────────────────────────────────────────────────────────────┐
    # │ META OPTIONS - Model behavior settings                                   │
    # └──────────────────────────────────────────────────────────────────────────┘
    class Meta:
        ordering = ['-created_at']          # Latest first (descending order)
        verbose_name = 'Analysis Transaction'
        verbose_name_plural = 'Analysis Transactions'

    # ┌──────────────────────────────────────────────────────────────────────────┐
    # │ STRING REPRESENTATION - Admin panel mein kaise dikhega                   │
    # └──────────────────────────────────────────────────────────────────────────┘
    def __str__(self):
        return f"{self.user.username} - {self.agent_type} - {self.created_at}"
