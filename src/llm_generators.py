"""
LLM-powered generators for more realistic and contextual synthetic data
"""

from typing import Dict, Any, List
from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser
import json
import re
from .generators import FieldGenerator
from .models import FieldDefinition, DataType
from .groq_config import GroqConfig, GroqOptimizer

# Import ChatGroq only when needed to avoid compatibility issues
def get_chat_groq():
    try:
        from langchain_groq import ChatGroq
        return ChatGroq
    except ImportError:
        raise ImportError("langchain-groq is not installed. Run: pip install langchain-groq")


class LLMFieldGenerator(FieldGenerator):
    """Base class for LLM-powered field generators"""
    
    def __init__(self, llm=None, model_name: str = "llama3-8b-8192", temperature: float = 0.7):
        super().__init__()
        self.llm = llm or GroqConfig.create_llm(
            model_name=model_name,
            temperature=temperature
        )
    
    def generate_with_context(self, field_def: FieldDefinition, context: Dict[str, Any] = None) -> Any:
        """Generate value using LLM with contextual awareness"""
        raise NotImplementedError


class LLMPersonGenerator(LLMFieldGenerator):
    """Generate realistic person profiles using LLM"""
    
    def generate(self, field_def: FieldDefinition, context: Dict[str, Any] = None) -> str:
        # Create contextual prompt based on existing data
        existing_data = context.get("current_record", {}) if context else {}
        
        if field_def.name in ["first_name", "name"]:
            return self._generate_name(existing_data, context)
        elif field_def.name == "email":
            return self._generate_email(existing_data, context)
        elif field_def.name == "bio" or "description" in field_def.name:
            return self._generate_bio(existing_data, context)
        
        return super().generate(field_def, context)
    
    def _generate_name(self, existing_data: Dict, context: Dict) -> str:
        prompt_template = """Generate a realistic first name for a person.
        Context: {context}
        
        Requirements:
        - Return only the name, no explanation
        - Make it diverse and realistic
        - Consider cultural diversity
        
        Name:"""
        
        prompt = PromptTemplate(
            input_variables=["context"],
            template=GroqOptimizer.optimize_prompt_for_groq(prompt_template)
        )
        
        context_str = f"Age: {existing_data.get('age', 'unknown')}, Location: {existing_data.get('location', 'unknown')}"
        result = self.llm(prompt.format(context=context_str))
        return result.strip()
    
    def _generate_email(self, existing_data: Dict, context: Dict) -> str:
        name = existing_data.get("first_name", existing_data.get("name", "user"))
        if name and name != "user":
            # Generate email based on name
            base_name = re.sub(r'[^a-zA-Z]', '', name.lower())
            domains = ["gmail.com", "yahoo.com", "outlook.com", "company.com"]
            import random
            domain = random.choice(domains)
            return f"{base_name}{random.randint(1, 999)}@{domain}"
        
        return super().generate(field_def, context)
    
    def _generate_bio(self, existing_data: Dict, context: Dict) -> str:
        prompt = PromptTemplate(
            input_variables=["name", "age", "profession", "context"],
            template="""Generate a realistic 2-3 sentence professional bio for:
            Name: {name}
            Age: {age}
            Profession: {profession}
            Additional context: {context}
            
            Requirements:
            - Keep it professional and realistic
            - 2-3 sentences maximum
            - No quotes or explanations
            
            Bio:"""
        )
        
        name = existing_data.get("name", "John Doe")
        age = existing_data.get("age", "30")
        profession = existing_data.get("profession", existing_data.get("job_title", "Professional"))
        
        result = self.llm(prompt.format(
            name=name,
            age=age,
            profession=profession,
            context=str(existing_data)
        ))
        return result.strip()


class LLMProductGenerator(LLMFieldGenerator):
    """Generate realistic product data using LLM"""
    
    def generate(self, field_def: FieldDefinition, context: Dict[str, Any] = None) -> str:
        existing_data = context.get("current_record", {}) if context else {}
        
        if field_def.name == "product_name":
            return self._generate_product_name(existing_data, context)
        elif field_def.name == "description":
            return self._generate_product_description(existing_data, context)
        
        return super().generate(field_def, context)
    
    def _generate_product_name(self, existing_data: Dict, context: Dict) -> str:
        category = existing_data.get("category", "General")
        
        prompt = PromptTemplate(
            input_variables=["category"],
            template="""Generate a realistic product name for the category: {category}
            
            Requirements:
            - Make it sound like a real product
            - Keep it concise (2-5 words)
            - Don't include quotes or explanations
            
            Product name:"""
        )
        
        result = self.llm(prompt.format(category=category))
        return result.strip()
    
    def _generate_product_description(self, existing_data: Dict, context: Dict) -> str:
        product_name = existing_data.get("product_name", "Product")
        category = existing_data.get("category", "General")
        price = existing_data.get("price", "")
        
        prompt = PromptTemplate(
            input_variables=["product_name", "category", "price"],
            template="""Generate a compelling product description for:
            Product: {product_name}
            Category: {category}
            Price: ${price}
            
            Requirements:
            - 1-2 sentences
            - Highlight key features
            - Sound professional and marketable
            - No quotes or explanations
            
            Description:"""
        )
        
        result = self.llm(prompt.format(
            product_name=product_name,
            category=category,
            price=price
        ))
        return result.strip()


class LLMReviewGenerator(LLMFieldGenerator):
    """Generate realistic customer reviews using LLM"""
    
    def generate(self, field_def: FieldDefinition, context: Dict[str, Any] = None) -> str:
        existing_data = context.get("current_record", {}) if context else {}
        
        product_name = existing_data.get("product_name", "this product")
        rating = existing_data.get("rating", 4)
        
        sentiment = "positive" if rating >= 4 else "neutral" if rating >= 3 else "negative"
        
        prompt = PromptTemplate(
            input_variables=["product_name", "rating", "sentiment"],
            template="""Generate a realistic customer review for:
            Product: {product_name}
            Rating: {rating}/5 stars
            Sentiment: {sentiment}
            
            Requirements:
            - Write like a real customer
            - Match the rating sentiment
            - 1-3 sentences
            - Include specific details
            - No quotes around the review
            
            Review:"""
        )
        
        result = self.llm(prompt.format(
            product_name=product_name,
            rating=rating,
            sentiment=sentiment
        ))
        return result.strip()


class LLMContextualGenerator(LLMFieldGenerator):
    """Generate data with full contextual awareness across all fields"""
    
    def generate_complete_record(self, schema_fields: List[FieldDefinition], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a complete record with all fields contextually related"""
        
        # Build prompt for complete record generation
        field_descriptions = []
        for field in schema_fields:
            constraints = []
            if field.min_value is not None:
                constraints.append(f"min: {field.min_value}")
            if field.max_value is not None:
                constraints.append(f"max: {field.max_value}")
            if field.choices:
                constraints.append(f"choices: {field.choices}")
            
            constraint_str = f" ({', '.join(constraints)})" if constraints else ""
            field_descriptions.append(f"- {field.name}: {field.data_type.value}{constraint_str}")
        
        fields_text = "\n".join(field_descriptions)
        
        prompt = PromptTemplate(
            input_variables=["fields", "context"],
            template="""Generate realistic synthetic data for a record with these fields:
            {fields}
            
            Additional context: {context}
            
            Requirements:
            - Make all fields contextually consistent with each other
            - Return valid JSON format
            - Use realistic, diverse data
            - Ensure data types match requirements
            
            JSON:"""
        )
        
        context_str = str(context) if context else "None"
        result = self.llm(prompt.format(fields=fields_text, context=context_str))
        
        try:
            # Parse the JSON response
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback to line-by-line parsing
                return self._parse_fallback(result, schema_fields)
        except json.JSONDecodeError:
            return self._parse_fallback(result, schema_fields)
    
    def _parse_fallback(self, result: str, schema_fields: List[FieldDefinition]) -> Dict[str, Any]:
        """Fallback parser for non-JSON responses"""
        record = {}
        lines = result.split('\n')
        
        for line in lines:
            for field in schema_fields:
                if field.name.lower() in line.lower():
                    # Extract value after colon
                    if ':' in line:
                        value = line.split(':', 1)[1].strip().strip('"\'')
                        # Type conversion
                        if field.data_type == DataType.INTEGER:
                            try:
                                record[field.name] = int(value)
                            except ValueError:
                                record[field.name] = 1
                        elif field.data_type == DataType.FLOAT:
                            try:
                                record[field.name] = float(value)
                            except ValueError:
                                record[field.name] = 1.0
                        elif field.data_type == DataType.BOOLEAN:
                            record[field.name] = value.lower() in ['true', 'yes', '1']
                        else:
                            record[field.name] = value
                        break
        
        return record


# Factory integration
def register_llm_generators():
    """Register LLM generators with the factory"""
    from .generators import GeneratorFactory
    
    # Register specialized LLM generators
    GeneratorFactory.register_custom_generator("llm_person", LLMPersonGenerator())
    GeneratorFactory.register_custom_generator("llm_product", LLMProductGenerator())
    GeneratorFactory.register_custom_generator("llm_review", LLMReviewGenerator())
    GeneratorFactory.register_custom_generator("llm_contextual", LLMContextualGenerator())
