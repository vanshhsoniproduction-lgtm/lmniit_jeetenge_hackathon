from django.db import models
from django.conf import settings

class AnalysisTransaction(models.Model):
    AGENT_CATEGORIES = [
        ('GITHUB', 'GitHub Agent'),
        ('AUDIO', 'Audio Agent'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='analyses')
    category = models.CharField(max_length=20, choices=AGENT_CATEGORIES)
    agent_type = models.CharField(max_length=50) # e.g. 'summarize', 'pr_review', 'meeting_notes'
    
    # Inputs
    title = models.CharField(max_length=255, blank=True, null=True) # For audio title or Repo name
    input_text = models.TextField(blank=True, null=True) # Repo URL
    input_file = models.FileField(upload_to='uploads/audio/', blank=True, null=True) # Audio file
    
    # Outputs (Stored as JSON text)
    # Structure: { "summary": "...", "todos": [...], "deadlines": [...] }
    output_data = models.TextField(blank=True, null=True) 
    
    # Payment
    tx_hash = models.CharField(max_length=100, blank=True, null=True)
    cost = models.DecimalField(max_digits=20, decimal_places=18, default=0.001) # Storing ETH amount
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.agent_type} - {self.created_at}"
