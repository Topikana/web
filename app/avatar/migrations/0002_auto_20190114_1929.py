# Generated by Django 2.1.4 on 2019-01-14 19:29

import avatar.utils
import logging
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import economy.models
from avatar.utils import dhash, get_temp_image_file
from PIL import Image, ImageOps
from django.core.files.base import ContentFile
from io import BytesIO
import hashlib
import json


logger = logging.getLogger(__name__)

def resize_gh_avatars(apps, schema_editor):
    social_avatar_model = apps.get_model('avatar', 'SocialAvatar')
    for avatar in social_avatar_model.objects.all():
        try:
            avatar_img = ImageOps.fit(Image.open(BytesIO(avatar.png.read())), (215, 215), Image.ANTIALIAS)
            avatar.png.save(f'{avatar.profile.handle}.png', ContentFile(get_temp_image_file(avatar_img).getvalue()), save=True)
            avatar.save()
        except Exception as e:
            logger.error('Could not resize gh avatar pk (%s), error (%s)', avatar.pk, e)



def generate_hashes(apps, schema_editor):
    social_avatar_model = apps.get_model('avatar', 'SocialAvatar')
    for social_avatar in social_avatar_model.objects.all():
        try:
            social_avatar.hash = dhash(Image.open(social_avatar.png))
            social_avatar.save()
        except Exception as e:
            logger.error('Could not generate hash for gh avatar pk (%s), error (%s)', social_avatar.pk, e)
    custom_avatar_model = apps.get_model('avatar', 'CustomAvatar')
    for custom_avatar in custom_avatar_model.objects.all():
        try:
            custom_avatar.hash = hashlib.sha256((bytearray(json.dumps(custom_avatar.config, sort_keys=True), 'utf8'))).hexdigest()
            custom_avatar.save()
        except Exception as e:
            logger.error('Could not generate hash for custom avatar pk (%s), error (%s)', custom_avatar.pk, e)


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0008_remove_profile_avatar'),
        ('avatar', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL("create table avatar_avatar_tmp as select * from avatar_avatar;"),
        migrations.CreateModel(
            name='BaseAvatar',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(db_index=True, default=economy.models.get_time)),
                ('modified_on', models.DateTimeField(default=economy.models.get_time)),
                ('active', models.BooleanField(default=False)),
                ('svg', models.FileField(blank=True, help_text='The avatar SVG.', null=True, upload_to=avatar.utils.get_upload_filename)),
                ('png', models.ImageField(blank=True, help_text='The avatar PNG.', null=True, upload_to=avatar.utils.get_upload_filename)),
                ('hash', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.DeleteModel(
            name='Avatar',
        ),
        migrations.CreateModel(
            name='CustomAvatar',
            fields=[
                ('baseavatar_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='avatar.BaseAvatar')),
                ('recommended_by_staff', models.BooleanField(default=False)),
                ('config', django.contrib.postgres.fields.jsonb.JSONField(default=dict, help_text='The JSON configuration.')),
            ],
            options={
                'abstract': False,
            },
            bases=('avatar.baseavatar',),
        ),
        migrations.CreateModel(
            name='SocialAvatar',
            fields=[
                ('baseavatar_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='avatar.BaseAvatar')),
            ],
            options={
                'abstract': False,
            },
            bases=('avatar.baseavatar',),
        ),
        migrations.AddField(
            model_name='baseavatar',
            name='profile',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='avatar_baseavatar_related', to='dashboard.Profile'),
        ),
        migrations.RunSQL("alter table avatar_baseavatar add column source_avatar_id integer"),
        migrations.RunSQL("alter table avatar_baseavatar add column is_custom boolean"),
        migrations.RunSQL("insert into avatar_baseavatar (id, created_on, modified_on, svg, png, active, profile_id, hash, source_avatar_id, is_custom) select nextval('avatar_baseavatar_id_seq') as id, aa.created_on, aa.modified_on, aa.github_svg as svg, aa.png, aa.use_github_avatar as active, (select dp.id from dashboard_profile_tmp dp where dp.avatar_id = aa.id) as profile_id, ' ' as hash, aa.id as source_avatar_id, false as is_custom from avatar_avatar_tmp aa where (aa.png = '') IS NOT TRUE;"),
        migrations.RunSQL("insert into avatar_baseavatar (id, created_on, modified_on, svg, png, active, profile_id, hash, source_avatar_id, is_custom) select nextval('avatar_baseavatar_id_seq') as id, aa.created_on, aa.modified_on, aa.svg, aa.custom_avatar_png, not aa.use_github_avatar as active, (select dp.id from dashboard_profile_tmp dp where dp.avatar_id = aa.id) as profile_id, ' ' as hash, aa.id as source_avatar_id, true as is_custom from avatar_avatar_tmp aa where aa.config != '{}';"),
        migrations.RunSQL("insert into avatar_customavatar (baseavatar_ptr_id, recommended_by_staff, config) select ba.id as baseavatar_ptr_id, false asrecommended_by_staff, aa.config as config  from avatar_avatar_tmp aa join avatar_baseavatar ba on ba.source_avatar_id = aa.id where ba.is_custom = true"),
        migrations.RunSQL("insert into avatar_socialavatar (baseavatar_ptr_id) select id from avatar_baseavatar where is_custom = false"),
        migrations.RunSQL("alter table avatar_baseavatar drop column source_avatar_id"),
        migrations.RunSQL("alter table avatar_baseavatar drop column is_custom"),
        migrations.RunSQL("drop table avatar_avatar_tmp"),
        migrations.RunSQL("drop table dashboard_profile_tmp"),
        migrations.RunPython(resize_gh_avatars),
        migrations.RunPython(generate_hashes)
    ]