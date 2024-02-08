from django.db import models

# Create your models here.
class Author(models.Model):
    name = models.CharField(max_length=100)

class Author(models.Model):
    id = models.AutoField(primary_key=True)
    firstName = models.CharField(max_length=50, default='')
    lastName = models.CharField(max_length=50, default='')
    email = models.EmailField(default="unknown@example.com")
    password = models.CharField(max_length=255, default='') # This will be encripted
    github = models.CharField(max_length=100, default='')
    profileImage = models.ImageField(upload_to='server/profile_images/', null=True, blank=True)
    # for debugging:
    # def __str__(self):
    #     return f"{self.firstname} {self.lastname}"

class Comment(models.Model):
    cid = models.AutoField(primary_key=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)

class Like(models.Model):
    lid = models.AutoField(primary_key=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)

class FollowedBy(models.Model):
    id1 = models.ForeignKey(Author, related_name='follows', on_delete=models.CASCADE)
    id2 = models.ForeignKey(Author, related_name='followers', on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('id1', 'id2')

class Follows(models.Model):
    follower = models.ForeignKey(Author, related_name='follower_set', on_delete=models.CASCADE)
    followed = models.ForeignKey(Author, related_name='followed_set', on_delete=models.CASCADE)