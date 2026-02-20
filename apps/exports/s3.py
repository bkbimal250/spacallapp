import boto3
from django.conf import settings


class S3Service:
    @staticmethod
    def upload_file(file_path, object_name=None):
        """
        Upload a file to an S3 bucket
        """
        if object_name is None:
            object_name = file_path.split("/")[-1]

        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )

        try:
            s3_client.upload_file(file_path, settings.AWS_STORAGE_BUCKET_NAME, object_name)
            
            # Generate presigned URL
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': object_name},
                ExpiresIn=3600
            )
            return url
        except Exception as e:
            print(f"S3 Upload Error: {e}")
            return None
