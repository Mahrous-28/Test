from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from openai import OpenAI
from google_images_search import GoogleImagesSearch
from .models import Advertisement
from .serializer import AdvertisementSerializer
from google.cloud import vision
from google.cloud.vision_v1 import ImageAnnotatorClient
import os

class GenerateAdvertView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def analyze_image(self, image_file):
        try:
            # Create Google Vision client
            client = ImageAnnotatorClient()
            
            # Read the image file
            content = image_file.read()
            image = vision.Image(content=content)
            
            # Perform multiple types of detection for comprehensive analysis
            label_detection = client.label_detection(image=image)
            object_detection = client.object_detection(image=image)
            text_detection = client.text_detection(image=image)
            
            # Extract and organize the results
            analysis_results = {
                'labels': [label.description for label in label_detection.label_annotations],
                'objects': [obj.name for obj in object_detection.localized_object_annotations],
                'text': [text.description for text in text_detection.text_annotations[:1]],  # Get main text block
            }
            
            return analysis_results
            
        except Exception as e:
            print(f"Error in image analysis: {str(e)}")
            return None

    def post(self, request):
        try:
            ad_description = request.data.get('ad_description')
            img_description = request.data.get('img_description')
            image_file = request.FILES.get('image')
            
            if not ad_description or not img_description:
                return Response(
                    {'error': 'Missing description'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Analyze image if provided
            image_analysis = None
            if image_file:
                image_analysis = self.analyze_image(image_file)
                # Reset file pointer for later use
                image_file.seek(0)

            # Generate content using OpenAI
            client = OpenAI()
            
            # Create base context
            context = f"""
                Generate a marketplace-optimized product listing using these details:
                Product Description: {ad_description}
                Image Description: {img_description}
            """

            # Add image analysis if available
            if image_analysis:
                context += f"""
                Additional Context from Image Analysis:
                - Detected Objects: {', '.join(image_analysis['objects'])}
                - Image Labels: {', '.join(image_analysis['labels'])}
                - Detected Text: {', '.join(image_analysis['text'])}
                """

            completion = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": """
                        You are an expert e-commerce copywriter specializing in creating platform-optimized product listings. Your task is to generate highly specific, detailed advertisements that are perfectly suited for online marketplaces like Shopify, Facebook Marketplace, and Amazon.

                        Core Requirements:
                        1. Product Specificity:
                            - Extract and highlight ALL technical specifications from the product description
                            - For vehicles: Include year, make, model, mileage, transmission, fuel type, accident history, modifications
                            - For electronics: Include brand, model, storage, condition, included accessories
                            - For furniture: Include dimensions, materials, style, condition, assembly requirements
                            - For clothing: Include size, brand, material, condition, care instructions
                            - Adapt to any product category with relevant specific details

                        2. Structure (300-400 characters optimal for marketplace visibility):
                            - Start with a keyword-rich title that includes brand, model, and key feature
                            - Opening paragraph: Core features and unique selling points
                            - Middle section: Technical specifications in scannable format
                            - Closing: Condition statement and call-to-action

                        3. Marketplace Optimization:
                            - Use relevant category-specific keywords for searchability
                            - Include all critical product details in the first 150 characters
                            - Format text for mobile viewing with short paragraphs
                            - Avoid marketplace-prohibited terms and excessive punctuation

                        4. Writing Style:
                            - Clear, concise, and factual tone
                            - No marketing fluff or unnecessary adjectives
                            - Focus on specifications over subjective descriptions
                            - Use bullet points for technical details
                            - Include numerical values whenever possible

                        5. Must Include:
                            - Precise condition description
                            - Any defects or issues clearly stated
                            - Original price comparison when relevant
                            - Shipping/pickup information if provided
                            - Warranty or return terms if applicable

                        Remember: Your goal is to create a listing that could be posted on any major marketplace platform without modification, maximizing visibility while providing all necessary information for a buyer's decision.
                    """},
                    {"role": "user", "content": context}
                ]
            )

            # Search for images if no image was uploaded
            if not image_file:
                self.image_search(img_description)

            # Save to database
            advertisement = Advertisement.objects.create(
                description=ad_description,
                image_description=img_description,
                generated_content=completion.choices[0].message.content,
                image=image_file if image_file else None
            )

            serializer = AdvertisementSerializer(advertisement)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def image_search(self, description):
        api_key = os.environ.get('GOOGLE_API_KEY')
        cx = os.environ.get('GOOGLE_CX')
        path = os.environ.get('IMAGES_PATH')
        
        gis = GoogleImagesSearch(api_key, cx)
        search_params = {
            'q': description,
            'num': 2,
            'imgSize': 'medium',
            'imgColorType': 'color'
        }
        
        gis.search(
            search_params=search_params,
            path_to_dir=path
        )
        return gis.results()

# settings.py (add these settings)
# MEDIA_URL = '/media/'
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')