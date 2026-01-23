from django.contrib import admin
from .models import AnalysisTransaction

@admin.register(AnalysisTransaction)
class AnalysisTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'agent_type', 'cost', 'created_at')
    list_filter = ('category', 'agent_type', 'created_at')
    search_fields = ('user__username', 'input_text', 'title', 'tx_hash')
