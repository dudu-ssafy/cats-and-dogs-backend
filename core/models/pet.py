from django.db import models
import uuid
from django.conf import settings

class AnimalType(models.Model):
    """반려 동물 종류 (개, 고양이 등)"""
    name = models.CharField(
        '반려 동물 종류',
        max_length=50,
        unique=True,
    )

    class Meta:
        db_table = 'animal_type'
        verbose_name = '동물 종류'
        verbose_name_plural = '동물 종류들'

    def __str__(self):
        return self.name


class Breed(models.Model):
    """품종 (푸들, 코숏 등)"""
    animal_type = models.ForeignKey(
        AnimalType,
        on_delete = models.CASCADE,
        related_name='breeds',
        verbose_name='동물 종류'
    )
    name = models.CharField(
        '품종명',
        max_length=100,
        help_text='푸들, 코숏 등'
    )

    class Meta:
        db_table = 'breed'
        verbose_name = '품종'
        verbose_name_plural = '품종들'
        constraints = [
            models.UniqueConstraint(
                fields=['animal_type', 'name'],
                name='unique_breed_per_animal_type'
            )
        ]

    def __str__(self):
        return f"{self.animal_type.name} - {self.name}"


class Pet(models.Model):
    """반려동물"""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(
        '이름',
        max_length=100
    )
    birth_date = models.DateField(
        '생년월일',
        null=True,
        blank=True
    )
    breed = models.ForeignKey(
        Breed,
        on_delete=models.PROTECT,
        related_name='pets',
        verbose_name='품종'
    )
    owners = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='PetOwnership',
        related_name='pets',
        verbose_name='보호자들'
    )

    class Meta:
        db_table = 'pet'
        verbose_name = '반려동물'
        verbose_name_plural = '반려동물들'
        indexes = [
            models.Index(fields=['breed'])
        ]

    def __str__(self):
        return f"{self.name} ({self.breed})"

    @property
    def animal_type(self):
        """반려동물의 동물 종류 (개/고양이)"""
        return self.breed.animal_type


class PetOwnership(models.Model):
    """반려동물 소유권 중간 테이블"""
    pet = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        verbose_name='반려동물'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='보호자'
    )
    role = models.CharField(
        '역할',
        max_length=50,
        default='owner',
        help_text='owner, co-owner 등'
    )
    registered_at = models.DateTimeField(
        '등록일',
        auto_now_add=True
    )

    class Meta:
        db_table = 'pet_ownership'
        verbose_name = '반려동물 소유권'
        verbose_name_plural = '반려동물 소유권들'
        constraints = [
            models.UniqueConstraint(
                fields=['pet', 'owner'],
                name='unique_pet_owner'
            )
        ]

    def __str__(self):
        return f"{self.owner.username} - {self.pet.name} ({self.role})"
