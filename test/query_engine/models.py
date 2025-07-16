from django.db import models

class Advertisement(models.Model):
    description = models.TextField()
    image_description = models.TextField()
    generated_content = models.TextField()
    image = models.ImageField(upload_to='uploads/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Advertisement {self.id}"