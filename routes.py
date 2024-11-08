from flask import Flask,render_template,request,redirect,url_for,flash, session, jsonify
from flask_caching import *
from models import *
from app import app
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

def auth_required(func):
    @wraps(func)
    def inner(*args,**kwargs):
        if 'user_id' not in session:
            flash('You need to login first')
            return redirect(url_for('login'))
        return func(*args,**kwargs)
    return inner

@app.route('/')
@auth_required
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', user=User.query.get(session['user_id']))

@app.route('/profile')
@auth_required
def profile():
    return render_template('profile.html', user=User.query.get(session['user_id']))

@app.route('/profile',methods=['POST'])
@auth_required
def profile_post():
    user = User.query.get(session['user_id'])
    username=request.form.get('username')
    password = request.form.get('password')
    cpassword = request.form.get('cpassword')
    if username == '' or password == '' or cpassword == '':
        flash('Username or password cannot be empty')
        return redirect(url_for('profile'))
    if not user.check_password(cpassword):
        flash('Incorrect Password')
        return redirect(url_for('profile'))
    if User.query.filter_by(username = username).first() and username != user.username:
        flash('Username already exists')
        return redirect(url_for('profile'))
    user.username = username
    user.password = password
    db.session.commit()
    flash('Profile updated successfully')
    return redirect(url_for('profile')) 

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login',methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    if username == '' or password == '':
        flash('Username or password cannot be empty')
        return redirect(url_for('login'))
    user = User.query.filter_by(username=username).first()
    if not user:
        flash('Invalid username or password')
        return redirect(url_for('login'))
    elif not user.check_password(password):
        flash('Invalid username or password')
        return redirect(url_for('login'))
    else:
        session['user_id'] = user.id
        session['user_role'] = user.role
        flash('Login successful!', 'success')
        if user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif user.role == 'sponsor':
            return redirect(url_for('sponsor_dashboard'))
        elif user.role == 'influencer':
            return redirect(url_for('influencer_dashboard'))    
    return render_template('index.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route("/register", methods=['POST'])
def register_post():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')

    if username == '' or password == '':
        flash('Username or password cannot be empty')
        return redirect(url_for('register'))

    if User.query.filter_by(username=username).first():
        flash('Username already exists. Please choose another username.')
        return redirect(url_for('register'))

    user = User(username=username, password=password, role=role)
    db.session.add(user)
    db.session.commit()  # Commit to get the user ID

    # Add user to the corresponding table based on role
    if role == 'sponsor':
        sponsor = Sponsor(user_id=user.id)  # Assuming your Sponsor model has a foreign key to User
        db.session.add(sponsor)
    elif role == 'influencer':
        influencer = Influencer(user_id=user.id)  # Assuming your Influencer model has a foreign key to User
        db.session.add(influencer)

    db.session.commit()

    flash('Registration successful!')
    return redirect(url_for('login'))


@app.route("/admin_dashboard")
def admin_dashboard():
    # Count stats for users, campaigns, and ad requests
    total_users = User.query.count()
    total_sponsors = User.query.filter_by(role='sponsor').count()
    total_influencers = User.query.filter_by(role='influencer').count()
    total_campaigns = Campaign.query.count()
    total_ad_requests = AdRequest.query.count()

    # Fetch all users, campaigns, and ad requests
    users = User.query.all()
    campaigns = Campaign.query.all()
    ad_requests = AdRequest.query.all()

    return render_template('admin_dashboard.html',total_users=total_users,total_sponsors=total_sponsors,total_influencers=total_influencers,total_campaigns=total_campaigns,total_ad_requests=total_ad_requests,users=users,campaigns=campaigns,ad_requests=ad_requests)

@app.route('/sponsor_dashboard')
def sponsor_dashboard():
    if 'user_id' not in session or session['user_role'] != 'sponsor':
        return redirect(url_for('login'))
    user_id = session['user_id']
    campaigns = Campaign.query.filter_by(sponsor_id=user_id).all()
    campaign_ad_requests = {}
    
    for campaign in campaigns:
        ad_requests = AdRequest.query.filter_by(campaign_id=campaign.id).all()
        campaign_ad_requests[campaign.id] = ad_requests
    
    return render_template('sponsor_dashboard.html', campaigns=campaigns, campaign_ad_requests=campaign_ad_requests)

@app.route('/influencer_dashboard')
def influencer_dashboard():
    if 'user_id' not in session or session['user_role'] != 'influencer':
        return redirect(url_for('login'))
    user_id = session['user_id']
    ad_requests = AdRequest.query.filter_by(influencer_id=user_id).all()
    return render_template('influencer_dashboard.html', ad_requests=ad_requests)

@app.route('/create_campaign')
def create_campaign_post():
    if 'user_id' not in session or session['user_role'] != 'sponsor':
        return redirect(url_for('login'))
    return render_template('create_campaign.html')

@app.route('/create_campaign', methods=['GET', 'POST'])
def create_campaign():
    if request.method == 'POST':
        # Your logic to create a campaign
        name = request.form.get('name')
        description = request.form.get('description')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        budget = request.form.get('budget')
        visibility = request.form.get('visibility')
        goals = request.form.get('goals')
        sponsor_id = session['user_id']


        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        # Create and save the campaign
        campaign = Campaign(name=name, description=description, start_date=start_date, end_date=end_date, budget=budget, visibility=visibility, goals=goals, sponsor_id=sponsor_id)
        db.session.add(campaign)
        db.session.commit()

        flash('Campaign created successfully!', 'success')
        return redirect(url_for('sponsor_dashboard'))
    
    return render_template('create_campaign.html')

@app.route('/edit_campaign/<int:campaign_id>', methods=['GET', 'POST'])
@auth_required
def edit_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)

    if campaign.sponsor_id != session['user_id']:
        flash('You are not authorized to edit this campaign.', 'danger')
        return redirect(url_for('sponsor_dashboard'))

    if request.method == 'POST':
        campaign.name = request.form.get('name')
        campaign.description = request.form.get('description')
        campaign.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        campaign.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
        campaign.budget = request.form.get('budget')
        campaign.visibility = request.form.get('visibility')
        campaign.goals = request.form.get('goals')

        db.session.commit()
        flash('Campaign updated successfully!', 'success')
        return redirect(url_for('sponsor_dashboard'))

    return render_template('edit_campaign.html', campaign=campaign)


@app.route('/delete_campaign/<int:campaign_id>', methods=['POST'])
@auth_required
def delete_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)

    # Ensure that the user is the sponsor of the campaign
    if campaign.sponsor_id != session['user_id']:
        flash('You are not authorized to delete this campaign.', 'danger')
        return redirect(url_for('sponsor_dashboard'))

    db.session.delete(campaign)
    db.session.commit()
    flash('Campaign deleted successfully!', 'success')
    return redirect(url_for('sponsor_dashboard'))

@app.route('/api/campaigns')
def get_campaigns():
    campaigns = Campaign.query.all()
    campaigns_data = [{
        'id': campaign.id,
        'name': campaign.name,
        'description': campaign.description,
        'start_date': campaign.start_date.strftime('%Y-%m-%d'),
        'end_date': campaign.end_date.strftime('%Y-%m-%d'),
    } for campaign in campaigns]

    return {'campaigns': campaigns_data}

@app.route('/create_ad_request', methods=['GET', 'POST'])
def create_ad_request():
    if request.method == 'POST':
        # Your logic to create a campaign
        campaign_id = request.form.get('campaign_id')
        requirements = request.form.get('requirements')
        payment_amount = request.form.get('payment_amount')
        status = request.form.get('status')
        influencer_id = session['user_id']


       # Create and save the campaign
        ad_request = AdRequest(influencer_id=influencer_id, campaign_id=campaign_id,requirements=requirements, payment_amount=payment_amount,status=status)
        db.session.add(ad_request)
        db.session.commit()

        flash('Ad Request created successfully!', 'success')
        return redirect(url_for('sponsor_dashboard'))
    
    return render_template('create_ad_request.html')


@app.route('/edit_ad_request/<int:ad_request_id>', methods=['GET', 'POST'])
@auth_required
def edit_ad_request(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    
    if ad_request.campaign.sponsor_id != session['user_id']:
        flash('You are not authorized to edit this ad request.', 'danger')
        return redirect(url_for('sponsor_dashboard'))

    if request.method == 'POST':
        ad_request.influencer_id = request.form.get('influencer_id')
        ad_request.requirements = request.form.get('requirements')
        ad_request.payment_amount = request.form.get('payment_amount')
        ad_request.status = request.form.get('status')
        db.session.commit()
        flash('Ad request updated successfully!', 'success')
        return redirect(url_for('sponsor_dashboard'))

    influencers = Influencer.query.all()  # To populate the dropdown of influencers
    return render_template('edit_ad_request.html', ad_request=ad_request, influencers=influencers)

@app.route('/delete_ad_request/<int:ad_request_id>', methods=['POST'])
@auth_required
def delete_ad_request(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    
    if ad_request.campaign.sponsor_id != session['user_id']:
        flash('You are not authorized to delete this ad request.', 'danger')
        return redirect(url_for('sponsor_dashboard'))

    db.session.delete(ad_request)
    db.session.commit()
    flash('Ad request deleted successfully!', 'success')
    return redirect(url_for('sponsor_dashboard'))


@app.route('/search_campaign')
def search_campaign():
    query = request.args.get('query')
    campaigns = Campaign.query.filter(Campaign.name.like('%' + query + '%')).all()
    return render_template('search_campaign.html', campaigns=campaigns)

@app.route('/search_influencer', methods=['GET', 'POST'])
@auth_required
def search_influencers():
    if 'user_role' not in session or session['user_role'] != 'sponsor':
        return redirect(url_for('login'))

    influencers = []
    if request.method == 'POST':
        niche = request.form.get('niche')
        min_reach = request.form.get('min_reach')
        max_reach = request.form.get('max_reach')

        query = Influencer.query

        if niche:
            query = query.filter(Influencer.niche.ilike(f'%{niche}%'))
        if min_reach:
            query = query.filter(Influencer.reach >= int(min_reach))
        if max_reach:
            query = query.filter(Influencer.reach <= int(max_reach))

        influencers = query.all()

    return render_template('search_influencer.html', influencers=influencers)



@app.route("/logout")
def logout():
    session.pop('user_id', None)
    session.pop('user_role', None)
    flash('You have been logged out')
    return redirect(url_for('login'))
