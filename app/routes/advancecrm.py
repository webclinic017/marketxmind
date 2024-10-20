from flask import Blueprint, request, jsonify, render_template, redirect, url_for,  flash, current_app
from app import db
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.loyalty import LoyaltyProgram, LoyaltyTier, CustomerLoyalty, ReferralProgram
from app.models.campaign import Campaign, CampaignMetric
from app.models.feedback import CustomerFeedback
from app.forms.advancecrm import LoyaltyProgramForm, CampaignForm, FeedbackForm
from app.utilities.utils import send_whatsapp_message, send_whatsapp_image, send_whatsapp_pdf
from app.utilities.utils import format_phone_number
from datetime import datetime, timedelta
from config import Config
import os
from math import ceil
from sqlalchemy import func, case, and_
from sqlalchemy.exc import IntegrityError,DataError
from sqlalchemy.sql import extract
from PIL import Image
import base64
import logging
import matplotlib.pyplot as plt
import io
import plotly.graph_objs as go
import pandas as pd
from openai import OpenAI
from transformers import pipeline, LlamaTokenizer, LlamaForCausalLM
import torch
advancecrm = Blueprint('advancecrm', __name__)


MODEL_NAME = Config.AIML_MODEL_NAME
ENDPOINT = Config.AIML_ENDPOINT
API_KEY = Config.AIML_API_KEY
client = OpenAI(
    api_key=API_KEY,
    base_url=ENDPOINT,
)

 
model_id = 'meta-llama/Llama-3.2-1B-Instruct'
try :
    pipe = pipeline(
        'text-generation',
        model=model_id,
        torch_dtype=torch.bfloat16,
        device_map='auto'
    )
except Exception as e:
    pipe = None
     

conversation = [
    {"role": "system", "content": "You are a business analyst specializing in customer loyalty and engagement strategies." }
]

def inital_user_prompt():
   
    program_total = db.session.query(func.count(LoyaltyProgram.id)).scalar()
    if not program_total :
        program_total=0
    tier_total = db.session.query(func.count(LoyaltyTier.id)).scalar()

    if not tier_total :
        tier_total=0
        
    customer_total = db.session.query(func.count(Customer.id)).scalar()
    campaign_total = db.session.query(func.count(Campaign.id)).filter(
        Campaign.is_active == True
    ).scalar()
     
    current_month = func.extract('month', Payment.created_date)
    current_year = func.extract('year', Payment.created_date)
    monthly_revenue = db.session.query(func.sum(Payment.amount)).filter(
        current_month == extract('month', func.now()),
        current_year == extract('year', func.now())
    ).scalar()
    
    current_month = func.extract('month', Invoice.created_date)
    current_year = func.extract('year', Invoice.created_date)
    monthly_omzet = db.session.query(func.sum(Invoice.net_amount)).filter(
        current_month == extract('month', func.now()),
        current_year == extract('year', func.now())
    ).scalar()

    churn_risk = calculate_churn_risk()  

    system_prompt = f"""
    You are a business analyst specializing in customer loyalty and engagement strategies. You have access to the following data:
    Customer total: {customer_total}
        - Monthly revenue: {monthly_revenue}
        - Monthly omzet: {monthly_omzet}
        - Churn Risk: {churn_risk}%
    Based on this data, please perform the following tasks:
    1.Analyze the current state of customer loyalty and engagement.
    2. Identify key challenges or areas of concern that may impact customer retention.
    3. Provide a list of actionable recommendations to improve customer loyalty programs and enhance customer engagement.
    """

    return system_prompt

def detailed_promp(point_id):
   
    program_total = db.session.query(func.count(LoyaltyProgram.id)).scalar() or 0
    tier_total = db.session.query(func.count(LoyaltyTier.id)).scalar() or 0
    customer_total = db.session.query(func.count(Customer.id)).scalar()
    
    churn_risk = calculate_churn_risk()  
  
    detailed_prompt = f"""
    Deeper and more detailed analysis to implement an increase in points {point_id} at company {current_user.company.name} 
    with number of customers {customer_total} and churn Risk: {churn_risk}%
    Also provide examples and tactical recommendations and metrics that can be obtained within a certain time period.
    Return only the code in your reply and should be represented as a visually appealing HTML div.
    Following structure and for each point and display icon fa-solid that is relevant to content each point for each header :
    <h6><a href="javascript:void(0);"  onclick="getDetailedPoint({{ key_point }})">{{ key_point }}</a></h6>
	<p>{{ detail_point }}</p>
	</div>
    """
    return detailed_prompt
@advancecrm.route('/advancecrm/advisor-llama')
def advisor_llama():
    return render_template('/advancecrm/advisor_llama.html')

@advancecrm.route('/advancecrm/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        user_input = request.json.get('message')
        
        if user_input:
            conversation.append({"role": "user", "content": user_input})

            try:
                # Generate the assistant's response
                outputs = pipe(conversation, max_new_tokens=256)
                assistant_response = outputs[0]['generated_text'].strip()

                # Add the response to the conversation
                conversation.append({"role": "assistant", "content": assistant_response})
                return jsonify({"response": assistant_response})
            except Exception as e:
                return jsonify({"response": "error"})
        else:
            return jsonify({"response": "Please enter a valid message."})
    else:
        # Render the chat page for GET requests
        return render_template('advancecrm/chat.html', conversation=conversation)
      
@advancecrm.route('/advancecrm')
def dashboard():

    program_total = db.session.query(func.count(LoyaltyProgram.id)).scalar()

    if not program_total :
        program_total=0
    
    tier_total = db.session.query(func.count(LoyaltyTier.id)).scalar()
    if not tier_total :
        tier_total=0
        
    customer_total = db.session.query(func.count(Customer.id)).scalar()
    campaign_total = db.session.query(func.count(Campaign.id)).filter(
        Campaign.is_active == True
    ).scalar()
    
    current_month = func.extract('month', Payment.created_date)
    current_year = func.extract('year', Payment.created_date)
    monthly_revenue = db.session.query(func.sum(Payment.amount)).filter(
        current_month == extract('month', func.now()),
        current_year == extract('year', func.now())
    ).scalar()
    
    current_month = func.extract('month', Invoice.created_date)
    current_year = func.extract('year', Invoice.created_date)
    monthly_omzet = db.session.query(func.sum(Invoice.net_amount)).filter(
        current_month == extract('month', func.now()),
        current_year == extract('year', func.now())
    ).scalar()
    
    churn_risk = calculate_churn_risk()  
    
           
    return render_template('advancecrm/dashboard.html', 
                            customer_total=customer_total, 
                            monthly_revenue=monthly_revenue,
                            monthly_omzet =monthly_omzet,
                            churn_risk=churn_risk,
                            program_total=program_total,
                            tier_total=tier_total,
                            campaign_total=campaign_total
                            )
                           
def calculate_churn_risk():
    today = datetime.today().date()
    start_of_period = today.replace(day=1) - timedelta(days=1)
    start_of_period = start_of_period.replace(day=1) 

    subquery = (
        db.session.query(
            Invoice.customer_id,
            func.max(Invoice.created_date).label('last_purchase_date')
        )
        .group_by(Invoice.customer_id)
        .subquery()
    )

    result = db.session.query(
        func.count(Customer.id),  # Total customers
        func.count(
            func.nullif(subquery.c.last_purchase_date > start_of_period, False)
        )  
    ).outerjoin(subquery, Customer.id == subquery.c.customer_id).first()

    total_customers, retained_customers = result

    if total_customers == 0:
        return 0 

    lost_customers = total_customers - retained_customers

    churn_rate = (lost_customers / total_customers) * 100
    return round(churn_rate, 2)
    
@advancecrm.route('/advancecrm/recommendations') 
def generate_recommendations():

    
    program_count = db.session.query(func.count(LoyaltyProgram.id)).all()
    program_total = program_count.scalar()
    if not program_total :
        program_total=0
    tier_count = db.session.query(func.count(LoyaltyTier.id)).all()
    tier_total = tier_count.scalar()
    if not tier_total :
        tier_total=0
        
    customer_query = db.session.query(func.count(Customer.id)).all()
    customer_total = customer_query.scalar()

    
    campaign_query = db.session.query(func.count(Campaign.id)).filter(
        Campaign.is_active == True
    )
    campaign_total = campaign_query.scalar()

    
    current_month = func.extract('month', Payment.created_date)
    current_year = func.extract('year', Payment.created_date)
    revenue_query = db.session.query(func.sum(Payment.amount)).filter(
        current_month == extract('month', func.now()),
        current_year == extract('year', func.now())
    )
    monthly_revenue = revenue_query.scalar()
    
    current_month = func.extract('month', Invoice.created_date)
    current_year = func.extract('year', Invoice.created_date)
    omzet_query = db.session.query(func.sum(Invoice.net_amount)).filter(
        current_month == extract('month', func.now()),
        current_year == extract('year', func.now())
    )
    monthly_omzet = omzet_query.scalar()

    churn_risk = calculate_churn_risk()  
    
    
    #try:
        
    prompt = f"""
    Analyze a CRM system for a  loyalty program 
    that has data :
    Customer total: {customer_total}
    Current monthly revenue : {monthly_revenue}
    Current monthly omzet : {monthly_omzet}
    Churn Rate: {churn_risk}%
    Provide Analyze and recommendations in bahasa Indonesia for creating targeted marketing campaigns using email, SMS, and WhatsApp. 
    Focus on creating customer loyalty programs, offering referral incentives, and personalizing follow-up interactions to reduce churn
    Suggest how to optimize the s\campaign notifications, targeted discounts and promotions, taking into account customer activity and purchase behavior

    Your reply should be represented as a visually appealing HTML div with the following structure:

    <div class="row g-2 rtl-flex-d-row-r">
            <div class="col-12">
                <div class="card">
                    <div class="card-header"><h5 class="mb-0">Rekomendasi AI</h5></div>
                    <div class="card-body"></div>
                </div>
            </div>
    </div>>
    Design Specifications:  professional, modern layout with hover effects to enhance interactivity and easy readability and engagement.

    Return only the code in your reply.

    """


    completion = client.chat.completions.create(
        model=MODEL_NAME,
         messages=[{
            "role": "user",
            "content": prompt,
        }],
    )
    print (completion)
    recommendation = completion.choices[0].message.content

    #except Exception as e:
     #   recommendation= ""
    recommendation = recommendation.replace("`", "").replace("html", "")
    return render_template('advancecrm/rekomendasi.html', 
                            recommendation=recommendation)

@advancecrm.route('/advancecrm/advisor')
def advisor():
    
    program_total = db.session.query(func.count(LoyaltyProgram.id)).scalar()
    if not program_total :
        program_total=0
    tier_total = db.session.query(func.count(LoyaltyTier.id)).scalar()

    if not tier_total :
        tier_total=0
        
    customer_total = db.session.query(func.count(Customer.id)).scalar()
    campaign_total = db.session.query(func.count(Campaign.id)).filter(
        Campaign.is_active == True
    ).scalar()
     
    current_month = func.extract('month', Payment.created_date)
    current_year = func.extract('year', Payment.created_date)
    monthly_revenue = db.session.query(func.sum(Payment.amount)).filter(
        current_month == extract('month', func.now()),
        current_year == extract('year', func.now())
    ).scalar()
    
    current_month = func.extract('month', Invoice.created_date)
    current_year = func.extract('year', Invoice.created_date)
    monthly_omzet = db.session.query(func.sum(Invoice.net_amount)).filter(
        current_month == extract('month', func.now()),
        current_year == extract('year', func.now())
    ).scalar()

    churn_risk = calculate_churn_risk()  

    # AI prompt
    initial_prompt = f"""
    Analyze a CRM system  with data:
    - Customer total: {customer_total}
    - Monthly revenue: {monthly_revenue}
    - Monthly omzet: {monthly_omzet}
    - Churn Risk: {churn_risk}%
    Provide analysis and recommendations to improve loyalty programs and customer engagement.
    Provide analysis and recommendations in list of key point with detail explain for each key point 
    Return only the code in your reply and should be represented as a visually appealing HTML card.
    Display Data and Then Display analysis and recommendations Following structure for each key point  and display icon fa-solid that relavance with content each point for each card header :
    <div class="card">
		<div class="card-header"><h5 class="mb-0"><a href="javascript:void(0);"  onclick="getDetailedPoint({{ key_point }})">{{ key_point }}</a></h5></div>
		<div class="card-body"><p>{{ detail_point }}</p></div>
	</div>
                           
    """

    #try:
    completion = client.chat.completions.create(
    model=Config.AIML_MODEL_NAME_OPENAI,
     messages=[{
        "role": "user",
        "content": initial_prompt,
        }],
        max_tokens=5000,
    )
    recommendation = completion.choices[0].message.content
    recommendation = recommendation.replace("`", "").replace("html", "")
    '''
    except Exception as e:
        recommendation = "<p>Tidak dapat menghasilkan rekomendasi saat ini. Silakan coba lagi nanti.</p>"
    '''
    return render_template('advancecrm/advisor.html', recommendations=recommendation)
    
@advancecrm.route('/advancecrm/advisor/detailed-point/<string:point_id>')
def advisor_detailed_point(point_id):
    program_total = db.session.query(func.count(LoyaltyProgram.id)).scalar() or 0
    tier_total = db.session.query(func.count(LoyaltyTier.id)).scalar() or 0
    customer_total = db.session.query(func.count(Customer.id)).scalar()
    
    churn_risk = calculate_churn_risk()  
    '''
    # Campaigns
    campaign_total = db.session.query(func.count(Campaign.id)).filter_by(company_id=company_id, is_active=True).scalar()

    # Monthly revenue and transaction counts
    current_month = func.extract('month', func.now())
    current_year = func.extract('year', func.now())

    monthly_revenue = db.session.query(func.count(TransactionCrm.id)).filter(
        TransactionCrm.company_id == company_id,
        func.extract('month', TransactionCrm.date) == current_month,
        func.extract('year', TransactionCrm.date) == current_year,
        TransactionCrm.is_rewarded == True
    ).scalar()

    monthly_omzet = db.session.query(func.count(TransactionCrm.id)).filter(
        TransactionCrm.company_id == company_id,
        func.extract('month', TransactionCrm.date) == current_month,
        func.extract('year', TransactionCrm.date) == current_year
    ).scalar()
    '''
    churn_risk = calculate_churn_risk()  
  
    detailed_prompt_id = f"""
    Analisa lebih dalam dan rinci  untuk melaksanakan peningkatan poin {point_id} pada perusahaan {current_user.company.name} 
    dengan jumlah pelanggan {customer_total} dan churn Risk: {churn_risk}%
    Tentang {current_user.company.name}  : {company.about}
    Berikan juga contoh dan rekomendasi taktis dan metrik yang dapat diperoleh dalam jangka waktu tertentu.
    Return only the code in your reply and should be represented as a visually appealing HTML div.
    Following structure and for each point and display icon fa-solid that relavance with content each point for each header :
    <h6><a href="javascript:void(0);"  onclick="getDetailedPoint({{ key_point }})">{{ key_point }}</a></h6>
	<p>{{ detail_point }}</p>
	</div>
    """
    detailed_prompt_en = f"""
    Deeper and more detailed analysis to implement an increase in points {point_id} at company {current_user.company.name} 
    with number of customers {customer_total} and churn Risk: {churn_risk}%
    About {current_user.company.name} : {company.about}
    Also provide examples and tactical recommendations and metrics that can be obtained within a certain time period.
    Return only the code in your reply and should be represented as a visually appealing HTML div.
    Following structure and for each point and display icon fa-solid that is relevant to content each point for each header :
    <h6><a href="javascript:void(0);"  onclick="getDetailedPoint({{ key_point }})">{{ key_point }}</a></h6>
	<p>{{ detail_point }}</p>
	</div>
    """
    #try:
        
    completion = client.chat.completions.create(
    model=Config.AIML_MODEL_NAME_OPENAI,
     messages=[{
        "role": "user",
        "content": detailed_prompt_en,
        }],
        max_tokens=5000,
    )

    detailed_response = completion.choices[0].message.content
    detailed_response = detailed_response.replace("`", "").replace("html", "").replace("*", "").replace("#", "")
    #except Exception as e:
    #    detailed_response = "<p>Tidak dapat menghasilkan detail rekomendasi saat ini. Silakan coba lagi nanti.</p>"

    return jsonify(detailed_response=detailed_response)

 
  