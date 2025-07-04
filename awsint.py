import boto3
import os
from botocore.exceptions import ClientError, NoCredentialsError
import logging
from datetime import datetime, timedelta
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AWSIntegration:
    """AWS Integration class for Capture Moments photography website"""

    def __init__(self):
        """Initialize AWS clients"""
        try:
            # AWS credentials should be set via environment variables or AWS credentials file
            self.s3_client = boto3.client('s3')
            self.ses_client = boto3.client('ses', region_name='ap-south-1')  # Mumbai region
            self.sns_client = boto3.client('sns', region_name='ap-south-1')
            
            # Configuration
            self.bucket_name = os.environ.get('AWS_S3_BUCKET', 'capture-moments-photos')
            self.region_name = 'ap-south-1'  # Mumbai region for Indian users
            
            logger.info("AWS Integration initialized successfully")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure AWS credentials.")
            raise
        except Exception as e:
            logger.error(f"Error initializing AWS Integration: {str(e)}")
            raise
    
    def upload_photo(self, file_path, file_name, metadata=None):
        """
        Upload photo to S3 bucket
        
        Args:
            file_path (str): Local path to the file
            file_name (str): Name for the file in S3
            metadata (dict): Additional metadata for the file
            
        Returns:
            str: S3 URL of uploaded file or None if failed
        """
        try:
            # Create metadata
            s3_metadata = {
                'upload_date': datetime.now().isoformat(),
                'photographer': metadata.get('photographer', 'Unknown') if metadata else 'Unknown',
                'event_type': metadata.get('event_type', 'General') if metadata else 'General',
                'location': metadata.get('location', 'India') if metadata else 'India'
            }
            
            # Upload file
            self.s3_client.upload_file(
                file_path, 
                self.bucket_name, 
                file_name,
                ExtraArgs={
                    'Metadata': s3_metadata,
                    'ContentType': 'image/jpeg',
                    'ACL': 'private'  # Keep photos private by default
                }
            )
            
            # Generate URL
            url = f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{file_name}"
            logger.info(f"Photo uploaded successfully: {url}")
            return url
            
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return None
        except ClientError as e:
            logger.error(f"Error uploading photo: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error uploading photo: {str(e)}")
            return None
    
    def generate_presigned_url(self, file_name, expiration=3600):
        """
        Generate presigned URL for private photo access
        
        Args:
            file_name (str): Name of the file in S3
            expiration (int): URL expiration time in seconds (default 1 hour)
            
        Returns:
            str: Presigned URL or None if failed
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': file_name},
                ExpiresIn=expiration
            )
            logger.info(f"Presigned URL generated for {file_name}")
            return url
            
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            return None
    
    def create_photo_gallery(self, event_id, photo_list):
        """
        Create a photo gallery by organizing photos in S3
        
        Args:
            event_id (str): Unique identifier for the event
            photo_list (list): List of photo file names
            
        Returns:
            dict: Gallery information
        """
        try:
            gallery_prefix = f"galleries/{event_id}/"
            gallery_urls = []
            
            for photo in photo_list:
                # Create presigned URL for each photo
                url = self.generate_presigned_url(f"{gallery_prefix}{photo}")
                if url:
                    gallery_urls.append({
                        'filename': photo,
                        'url': url,
                        'thumbnail_url': self.generate_presigned_url(f"{gallery_prefix}thumbnails/{photo}")
                    })
            
            gallery_info = {
                'event_id': event_id,
                'created_date': datetime.now().isoformat(),
                'photo_count': len(gallery_urls),
                'photos': gallery_urls,
                'access_code': f"CM{event_id[-6:].upper()}"  # Generate access code
            }
            
            logger.info(f"Photo gallery created for event {event_id} with {len(gallery_urls)} photos")
            return gallery_info
            
        except Exception as e:
            logger.error(f"Error creating photo gallery: {str(e)}")
            return None
    
    def send_notification_email(self, recipient_email, subject, message, sender_email='noreply@capturemoments.in'):
        """
        Send notification email using SES
        
        Args:
            recipient_email (str): Recipient email address
            subject (str): Email subject
            message (str): Email message
            sender_email (str): Sender email address
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create HTML email template
            html_template = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="background: #007bff; color: white; padding: 20px; text-align: center;">
                            <h1 style="margin: 0;">📸 Capture Moments</h1>
                        </div>
                        <div style="padding: 20px; background: #f8f9fa;">
                            <p>Namaste!</p>
                            <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                                {message}
                            </div>
                            <p>Best regards,<br>
                            Team Capture Moments</p>
                            <hr style="border: 1px solid #dee2e6;">
                            <p style="font-size: 12px; color: #6c757d;">
                                Capture Moments - Professional Photography Services across India<br>
                                Email: info@capturemoments.in | Phone: +91 98765 43210
                            </p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            response = self.ses_client.send_email(
                Source=sender_email,
                Destination={'ToAddresses': [recipient_email]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': {
                        'Html': {'Data': html_template, 'Charset': 'UTF-8'},
                        'Text': {'Data': message, 'Charset': 'UTF-8'}
                    }
                }
            )
            
            logger.info(f"Email sent successfully to {recipient_email}")
            return True
            
        except ClientError as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email: {str(e)}")
            return False
    
    def send_booking_confirmation(self, booking_details):
        """
        Send booking confirmation email
        
        Args:
            booking_details (dict): Booking information
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            recipient_email = booking_details.get('client_email')
            photographer_name = booking_details.get('photographer_name')
            service_type = booking_details.get('service_type')
            event_date = booking_details.get('event_date')
            location = booking_details.get('location')
            
            subject = f"Booking Confirmation - {service_type} with {photographer_name}"
            
            message = f"""
            <h2>Your booking has been confirmed!</h2>
            <p><strong>Booking Details:</strong></p>
            <ul>
                <li><strong>Photographer:</strong> {photographer_name}</li>
                <li><strong>Service:</strong> {service_type}</li>
                <li><strong>Date:</strong> {event_date}</li>
                <li><strong>Location:</strong> {location}</li>
            </ul>
            <p>Your photographer will contact you within 24 hours to discuss the details.</p>
            <p>Thank you for choosing Capture Moments!</p>
            """
            
            return self.send_notification_email(recipient_email, subject, message)
            
        except Exception as e:
            logger.error(f"Error sending booking confirmation: {str(e)}")
            return False
    
    def send_gallery_ready_notification(self, client_email, gallery_info):
        """
        Send notification when photo gallery is ready
        
        Args:
            client_email (str): Client email address
            gallery_info (dict): Gallery information
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            access_code = gallery_info.get('access_code')
            photo_count = gallery_info.get('photo_count')
            event_id = gallery_info.get('event_id')
            
            subject = "Your Photo Gallery is Ready! 📸"
            
            message = f"""
            <h2>Your beautiful memories are ready!</h2>
            <p>We're excited to share that your photo gallery is now ready for viewing.</p>
            
            <div style="background: #e7f3ff; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h3>Gallery Details:</h3>
                <ul>
                    <li><strong>Total Photos:</strong> {photo_count}</li>
                    <li><strong>Access Code:</strong> <span style="font-size: 18px; font-weight: bold; color: #007bff;">{access_code}</span></li>
                    <li><strong>Gallery ID:</strong> {event_id}</li>
                </ul>
            </div>
            
            <p>To view your gallery:</p>
            <ol>
                <li>Visit our website at <a href="https://capturemoments.in/gallery">capturemoments.in/gallery</a></li>
                <li>Enter your access code: <strong>{access_code}</strong></li>
                <li>Enjoy your beautiful memories!</li>
            </ol>
            
            <p>You can download high-resolution photos and share them with your loved ones.</p>
            <p>The gallery will be available for 30 days.</p>
            """
            
            return self.send_notification_email(client_email, subject, message)
            
        except Exception as e:
            logger.error(f"Error sending gallery notification: {str(e)}")
            return False
    
    def send_sms_notification(self, phone_number, message):
        """
        Send SMS notification using SNS
        
        Args:
            phone_number (str): Phone number in international format (+91XXXXXXXXXX)
            message (str): SMS message
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure phone number is in correct format
            if not phone_number.startswith('+91'):
                phone_number = f'+91{phone_number}'
            
            response = self.sns_client.publish(
                PhoneNumber=phone_number,
                Message=message
            )
            
            logger.info(f"SMS sent successfully to {phone_number}")
            return True
            
        except ClientError as e:
            logger.error(f"Error sending SMS: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending SMS: {str(e)}")
            return False
    
    def backup_database(self, db_file_path):
        """
        Backup database to S3
        
        Args:
            db_file_path (str): Path to database file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            backup_key = f"backups/database_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            
            self.s3_client.upload_file(
                db_file_path,
                self.bucket_name,
                backup_key,
                ExtraArgs={'StorageClass': 'STANDARD_IA'}  # Cheaper storage for backups
            )
            
            logger.info(f"Database backup completed: {backup_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error backing up database: {str(e)}")
            return False
    
    def get_usage_stats(self):
        """
        Get AWS usage statistics
        
        Returns:
            dict: Usage statistics
        """
        try:
            # Get S3 bucket size
            s3_response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            total_size = sum(obj['Size'] for obj in s3_response.get('Contents', []))
            total_objects = len(s3_response.get('Contents', []))
            
            stats = {
                'storage_used_bytes': total_size,
                'storage_used_mb': round(total_size / (1024 * 1024), 2),
                'total_photos': total_objects,
                'last_updated': datetime.now().isoformat()
            }
            
            logger.info(f"Usage stats retrieved: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting usage stats: {str(e)}")
            return None

# Example usage functions
def example_usage():
    """Example of how to use the AWS integration"""
    try:
        # Initialize AWS integration
        aws = AWSIntegration()
        
        # Example: Upload a photo
        photo_metadata = {
            'photographer': 'Rajesh Kumar',
            'event_type': 'Wedding',
            'location': 'Mumbai, Maharashtra'
        }
        
        # aws.upload_photo('local_photo.jpg', 'wedding_photos/photo1.jpg', photo_metadata)
        
        # Example: Send booking confirmation
        booking_details = {
            'client_email': 'client@example.com',
            'photographer_name': 'Rajesh Kumar',
            'service_type': 'Wedding Photography',
            'event_date': '2024-03-15',
            'location': 'Mumbai, Maharashtra'
        }
        
        # aws.send_booking_confirmation(booking_details)
        
        # Example: Create photo gallery
        # photo_list = ['photo1.jpg', 'photo2.jpg', 'photo3.jpg']
        # gallery = aws.create_photo_gallery('wedding_001', photo_list)
        
        # Example: Send SMS notification
        # aws.send_sms_notification('+919876543210', 'Your booking is confirmed!')
        
        # Example: Get usage stats
        stats = aws.get_usage_stats()
        print(f"Current usage: {stats}")
        
    except Exception as e:
        logger.error(f"Error in example usage: {str(e)}")

if __name__ == "__main__":
    example_usage()