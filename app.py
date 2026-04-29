from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Email
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
import json
import io
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'agricolect_secret_key_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agricolect.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==================== MODEL ====================
class CollecteAgricole(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_collecte = db.Column(db.DateTime, default=datetime.utcnow)
    nom_agriculteur = db.Column(db.String(100), nullable=False)
    region = db.Column(db.String(50), nullable=False)
    culture = db.Column(db.String(50), nullable=False)
    superficie_hectares = db.Column(db.Float, nullable=False)
    quantite_produite_kg = db.Column(db.Float, nullable=False)
    prix_vente_kg = db.Column(db.Float, nullable=False)
    depenses_total = db.Column(db.Float, nullable=False)
    saison = db.Column(db.String(50), nullable=False)
    methode_culture = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100))
    notes = db.Column(db.Text)
    
    def benefice_total(self):
        return (self.quantite_produite_kg * self.prix_vente_kg) - self.depenses_total
    
    def rendement_hectare(self):
        if self.superficie_hectares > 0:
            return self.quantite_produite_kg / self.superficie_hectares
        return 0

# ==================== FORM ====================
class CollecteForm(FlaskForm):
    nom_agriculteur = StringField('Farmer Name', validators=[DataRequired()])
    region = SelectField('Region', choices=[
        ('Adamawa', 'Adamawa'), ('Centre', 'Centre'), ('East', 'East'),
        ('Far North', 'Far North'), ('Littoral', 'Littoral'), ('North', 'North'),
        ('North West', 'North West'), ('West', 'West'), ('South', 'South'),
        ('South West', 'South West')
    ], validators=[DataRequired()])
    culture = SelectField('Crop', choices=[
        ('Maize', 'Maize'), ('Cassava', 'Cassava'), ('Cocoa', 'Cocoa'),
        ('Coffee', 'Coffee'), ('Banana', 'Banana'), ('Rice', 'Rice'),
        ('Groundnut', 'Groundnut'), ('Tomato', 'Tomato')
    ], validators=[DataRequired()])
    superficie_hectares = FloatField('Area (hectares)', validators=[DataRequired(), NumberRange(min=0.01)])
    quantite_produite_kg = FloatField('Production (kg)', validators=[DataRequired(), NumberRange(min=0)])
    prix_vente_kg = FloatField('Price (FCFA/kg)', validators=[DataRequired(), NumberRange(min=0)])
    depenses_total = FloatField('Total Expenses (FCFA)', validators=[DataRequired(), NumberRange(min=0)])
    saison = SelectField('Season', choices=[
        ('Small rainy season', 'Small rainy season'),
        ('Large rainy season', 'Large rainy season'),
        ('Dry season', 'Dry season'),
        ('Flood season', 'Flood season')
    ])
    methode_culture = SelectField('Farming Method', choices=[
        ('Traditional', 'Traditional'), ('Modern', 'Modern'),
        ('Organic', 'Organic'), ('Mixed', 'Mixed')
    ])
    email = StringField('Email', validators=[Email()])
    notes = TextAreaField('Notes')
    submit = SubmitField('Save Data')

# ==================== LICENCE INFORMATION ====================
LICENSE_INFO = {
    'licensee': 'NGWANYA NORA SHEI',
    'matricule': '24G2586',
    'university': 'University of Yaoundé I (UY1)',
    'faculty': 'Faculty of Science',
    'department': 'Computer Science',
    'course': 'INF232 EC2 - Data Analysis',
    'project': 'AgriCollect Cameroon - Agricultural Data Collection Platform',
    'license_type': 'Professional Academic License',
    'version': '2.0',
    'year': '2024',
    'expiry': 'Lifetime Academic Use',
    'features': [
        'Data Collection & Management',
        'Linear Regression Analysis',
        'K-Means Clustering Classification',
        'Interactive Dashboards',
        'Dynamic Filters',
        'Farmer Comparison Tool',
        'AI-Based Recommendations',
        'Data Import/Export (CSV/Excel)',
        'Predictive Analytics',
        'Advanced Visualizations'
    ]
}

# ==================== ROUTES ====================

@app.route('/')
def index():
    total = CollecteAgricole.query.count()
    farmers = db.session.query(CollecteAgricole.nom_agriculteur).distinct().count()
    cultures = db.session.query(CollecteAgricole.culture).distinct().count()
    dernieres = CollecteAgricole.query.order_by(CollecteAgricole.date_collecte.desc()).limit(5).all()
    return render_template('index.html', 
                          stats={'total_entries': total, 'total_farmers': farmers, 'cultures_unique': cultures},
                          dernieres=dernieres,
                          license=LICENSE_INFO)

@app.route('/collecte', methods=['GET', 'POST'])
def collecte():
    form = CollecteForm()
    if form.validate_on_submit():
        collecte = CollecteAgricole(
            nom_agriculteur=form.nom_agriculteur.data,
            region=form.region.data,
            culture=form.culture.data,
            superficie_hectares=form.superficie_hectares.data,
            quantite_produite_kg=form.quantite_produite_kg.data,
            prix_vente_kg=form.prix_vente_kg.data,
            depenses_total=form.depenses_total.data,
            saison=form.saison.data,
            methode_culture=form.methode_culture.data,
            email=form.email.data,
            notes=form.notes.data
        )
        db.session.add(collecte)
        db.session.commit()
        flash('Data saved successfully!', 'success')
        return redirect(url_for('collecte'))
    return render_template('collecte.html', form=form)

@app.route('/liste')
def liste():
    donnees = CollecteAgricole.query.order_by(CollecteAgricole.date_collecte.desc()).all()
    total_benefice = sum(d.benefice_total() for d in donnees)
    total_production = sum(d.quantite_produite_kg for d in donnees)
    return render_template('liste.html', donnees=donnees, total_benefice=total_benefice, total_production=total_production)

@app.route('/supprimer/<int:id>')
def supprimer(id):
    data = CollecteAgricole.query.get_or_404(id)
    db.session.delete(data)
    db.session.commit()
    flash('Data deleted successfully!', 'success')
    return redirect(url_for('liste'))

@app.route('/analyse')
def analyse():
    data = CollecteAgricole.query.all()
    if not data:
        return render_template('analyse.html', has_data=False)
    
    df = pd.DataFrame([{
        'culture': d.culture,
        'production': d.quantite_produite_kg,
        'benefice': d.benefice_total()
    } for d in data])
    
    stats = {
        'total_collectes': len(df),
        'agriculteurs': df['culture'].nunique(),
        'production_totale': df['production'].sum(),
        'benefice_moyen': df['benefice'].mean()
    }
    
    fig = px.bar(df.groupby('culture')['production'].sum().reset_index(), 
                 x='culture', y='production', title='Production by Crop')
    
    return render_template('analyse.html', has_data=True, stats=stats,
                          graph1=json.dumps(fig, cls=PlotlyJSONEncoder))

@app.route('/regression')
def regression():
    data = CollecteAgricole.query.all()
    if len(data) < 3:
        return render_template('regression.html', has_data=False, error="Minimum 3 records required")
    
    df = pd.DataFrame([{
        'superficie': d.superficie_hectares,
        'production': d.quantite_produite_kg,
        'benefice': d.benefice_total(),
        'culture': d.culture,
        'region': d.region,
        'depenses': d.depenses_total,
        'rendement': d.rendement_hectare()
    } for d in data])
    
    X = df[['superficie']].values
    y = df['production'].values
    reg = LinearRegression()
    reg.fit(X, y)
    
    x_range = np.linspace(df['superficie'].min(), df['superficie'].max(), 100).reshape(-1, 1)
    y_pred = reg.predict(x_range)
    
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df['superficie'], y=df['production'], mode='markers', 
                              name='Actual Data', marker=dict(size=10, color='green'),
                              text=df['culture'], hovertemplate='%{text}<br>Area: %{x} ha<br>Production: %{y:.0f} kg'))
    fig1.add_trace(go.Scatter(x=x_range.flatten(), y=y_pred, mode='lines', 
                              name=f'Regression Line (R² = {reg.score(X, y):.3f})',
                              line=dict(color='red', width=3)))
    fig1.update_layout(title='Linear Regression: Area vs Production', xaxis_title='Area (ha)', yaxis_title='Production (kg)', height=450)
    
    corr_df = df[['superficie', 'production', 'benefice', 'depenses', 'rendement']].corr()
    fig2 = go.Figure(data=go.Heatmap(z=corr_df.values, x=corr_df.columns, y=corr_df.columns, 
                                      colorscale='RdYlGn', text=corr_df.round(2).values, texttemplate='%{text}'))
    fig2.update_layout(title='Correlation Matrix', height=450)
    
    fig3 = px.bar(df.groupby('region')['production'].sum().reset_index(), x='region', y='production', 
                  title='Production by Region', color='region')
    fig4 = px.box(df, x='culture', y='rendement', color='culture', title='Yield Distribution by Crop (kg/ha)')
    fig4.update_layout(showlegend=False)
    
    stats = {
        'coefficient': reg.coef_[0],
        'intercept': reg.intercept_,
        'r2': reg.score(X, y)
    }
    
    predictions = []
    for area in [1, 2.5, 5, 10]:
        pred = reg.predict([[area]])[0]
        predictions.append({'superficie': area, 'production': round(pred, 0)})
    
    return render_template('regression.html', has_data=True, stats=stats, predictions=predictions,
                          graph1=json.dumps(fig1, cls=PlotlyJSONEncoder),
                          graph2=json.dumps(fig2, cls=PlotlyJSONEncoder),
                          graph3=json.dumps(fig3, cls=PlotlyJSONEncoder),
                          graph4=json.dumps(fig4, cls=PlotlyJSONEncoder))

@app.route('/classification')
def classification():
    data = CollecteAgricole.query.all()
    if len(data) < 5:
        return render_template('classification.html', has_data=False, error="Minimum 5 records required")
    
    df = pd.DataFrame([{
        'superficie': d.superficie_hectares,
        'production': d.quantite_produite_kg,
        'benefice': d.benefice_total(),
        'culture': d.culture
    } for d in data])
    
    X = df[['superficie', 'production', 'benefice']].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df['cluster'] = kmeans.fit_predict(X_scaled)
    
    fig = px.scatter(df, x='superficie', y='production', color=df['cluster'].astype(str),
                     hover_data=['culture', 'benefice'], title='K-Means Clustering of Farms')
    fig.update_layout(xaxis_title='Area (ha)', yaxis_title='Production (kg)')
    
    return render_template('classification.html', has_data=True, n_clusters=3,
                          graph1=json.dumps(fig, cls=PlotlyJSONEncoder))

@app.route('/dashboard')
def dashboard():
    data = CollecteAgricole.query.all()
    if not data:
        return render_template('dashboard.html', has_data=False)
    
    df = pd.DataFrame([{
        'culture': d.culture,
        'production': d.quantite_produite_kg,
        'benefice': d.benefice_total(),
        'region': d.region
    } for d in data])
    
    metrics = {
        'total_production': df['production'].sum(),
        'total_benefice': df['benefice'].sum(),
        'total_entries': len(df),
        'best_culture': df.groupby('culture')['production'].sum().idxmax(),
        'best_region': df.groupby('region')['production'].sum().idxmax()
    }
    
    fig1 = px.bar(df.groupby('culture')['production'].sum().reset_index().head(5), 
                  x='culture', y='production', title='Top 5 Crops by Production', color='culture')
    fig2 = px.pie(df, names='region', values='production', title='Production by Region')
    
    return render_template('dashboard.html', has_data=True, metrics=metrics,
                          graph1=json.dumps(fig1, cls=PlotlyJSONEncoder),
                          graph2=json.dumps(fig2, cls=PlotlyJSONEncoder))

@app.route('/filtres')
def filtres():
    region = request.args.get('region', '')
    culture = request.args.get('culture', '')
    
    query = CollecteAgricole.query
    if region:
        query = query.filter(CollecteAgricole.region == region)
    if culture:
        query = query.filter(CollecteAgricole.culture == culture)
    
    data = query.all()
    regions = [r[0] for r in db.session.query(CollecteAgricole.region.distinct()).all()]
    cultures = [c[0] for c in db.session.query(CollecteAgricole.culture.distinct()).all()]
    
    graph = None
    if data:
        df = pd.DataFrame([{'culture': d.culture, 'production': d.quantite_produite_kg} for d in data])
        fig = px.bar(df.groupby('culture')['production'].sum().reset_index(), x='culture', y='production', title='Filtered Production')
        graph = json.dumps(fig, cls=PlotlyJSONEncoder)
    
    return render_template('filtres.html', regions=regions, cultures=cultures, data=data, graph=graph, total=len(data))

@app.route('/comparaison')
def comparaison():
    agriculteurs = [a[0] for a in db.session.query(CollecteAgricole.nom_agriculteur).distinct().all()]
    agri1 = request.args.get('agri1', '')
    agri2 = request.args.get('agri2', '')
    
    data1 = CollecteAgricole.query.filter_by(nom_agriculteur=agri1).all() if agri1 else []
    data2 = CollecteAgricole.query.filter_by(nom_agriculteur=agri2).all() if agri2 else []
    
    stats1, stats2, graph = None, None, None
    
    if data1 and data2:
        stats1 = {
            'production': sum(d.quantite_produite_kg for d in data1),
            'benefice': sum(d.benefice_total() for d in data1),
            'nb': len(data1)
        }
        stats2 = {
            'production': sum(d.quantite_produite_kg for d in data2),
            'benefice': sum(d.benefice_total() for d in data2),
            'nb': len(data2)
        }
        
        fig = go.Figure()
        fig.add_trace(go.Bar(name=agri1, x=['Production', 'Benefit'], y=[stats1['production'], stats1['benefice']], marker_color='green'))
        fig.add_trace(go.Bar(name=agri2, x=['Production', 'Benefit'], y=[stats2['production'], stats2['benefice']], marker_color='blue'))
        fig.update_layout(title=f'Comparison: {agri1} vs {agri2}', barmode='group')
        graph = json.dumps(fig, cls=PlotlyJSONEncoder)
    
    return render_template('comparaison.html', agriculteurs=agriculteurs, agri1=agri1, agri2=agri2, 
                          stats1=stats1, stats2=stats2, graph=graph)

@app.route('/recommandations')
def recommandations():
    data = CollecteAgricole.query.all()
    if len(data) < 3:
        return render_template('recommandations.html', has_data=False)
    
    df = pd.DataFrame([{
        'culture': d.culture,
        'region': d.region,
        'benefice': d.benefice_total(),
        'methode': d.methode_culture
    } for d in data])
    
    best_by_region = df.groupby(['region', 'culture'])['benefice'].mean().reset_index()
    best_by_region = best_by_region.loc[best_by_region.groupby('region')['benefice'].idxmax()]
    best_method = df.groupby('methode')['benefice'].mean().idxmax()
    top_cultures = df.groupby('culture')['benefice'].mean().sort_values(ascending=False).head(3)
    
    recommendations = {
        'best_culture_by_region': best_by_region.to_dict('records'),
        'best_method': best_method,
        'top_cultures': top_cultures.to_dict()
    }
    
    return render_template('recommandations.html', has_data=True, recommendations=recommendations)

@app.route('/import', methods=['GET', 'POST'])
def import_data():
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename.endswith(('.csv', '.xlsx', '.xls')):
            try:
                if file.filename.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)
                
                count = 0
                for _, row in df.iterrows():
                    collecte = CollecteAgricole(
                        nom_agriculteur=str(row.get('nom_agriculteur', row.get('Name', 'Unknown'))),
                        region=str(row.get('region', row.get('Region', 'Centre'))),
                        culture=str(row.get('culture', row.get('Crop', 'Maize'))),
                        superficie_hectares=float(row.get('superficie_hectares', row.get('Area', 1))),
                        quantite_produite_kg=float(row.get('quantite_produite_kg', row.get('Production', 0))),
                        prix_vente_kg=float(row.get('prix_vente_kg', row.get('Price', 300))),
                        depenses_total=float(row.get('depenses_total', row.get('Expenses', 0))),
                        saison=str(row.get('saison', row.get('Season', 'Large rainy season'))),
                        methode_culture=str(row.get('methode_culture', row.get('Method', 'Traditional')))
                    )
                    db.session.add(collecte)
                    count += 1
                
                db.session.commit()
                flash(f'{count} records imported successfully!', 'success')
            except Exception as e:
                flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('liste'))
    
    return render_template('import.html')

@app.route('/visualisation')
def visualisation():
    data = CollecteAgricole.query.all()
    if not data:
        return render_template('visualisation.html', has_data=False)
    
    df = pd.DataFrame([{
        'culture': d.culture,
        'production': d.quantite_produite_kg,
        'benefice': d.benefice_total(),
        'region': d.region,
        'methode': d.methode_culture
    } for d in data])
    
    fig1 = px.box(df, x='culture', y='benefice', color='culture', title='Benefit Distribution by Crop')
    fig2 = px.scatter(df, x='production', y='benefice', color='methode', title='Production vs Benefit by Method', size='production')
    fig3 = px.bar(df.groupby('region')['production'].sum().reset_index(), x='region', y='production', title='Production by Region', color='region')
    
    return render_template('visualisation.html', has_data=True,
                          graph1=json.dumps(fig1, cls=PlotlyJSONEncoder),
                          graph2=json.dumps(fig2, cls=PlotlyJSONEncoder),
                          graph3=json.dumps(fig3, cls=PlotlyJSONEncoder))

@app.route('/predict')
def predict():
    data = CollecteAgricole.query.all()
    if len(data) < 3:
        return render_template('predict.html', has_data=False, error="Minimum 3 records required for prediction")
    
    df = pd.DataFrame([{'superficie': d.superficie_hectares, 'production': d.quantite_produite_kg} for d in data])
    reg = LinearRegression()
    reg.fit(df[['superficie']].values, df['production'].values)
    
    scenarios = [
        {'superficie': 1, 'label': '1 hectare'},
        {'superficie': 2.5, 'label': '2.5 hectares'},
        {'superficie': 5, 'label': '5 hectares'},
        {'superficie': 10, 'label': '10 hectares'}
    ]
    
    predictions = []
    for s in scenarios:
        pred = reg.predict([[s['superficie']]])[0]
        predictions.append({'label': s['label'], 'superficie': s['superficie'], 'production': round(pred, 0)})
    
    return render_template('predict.html', has_data=True, predictions=predictions, r2=reg.score(df[['superficie']].values, df['production'].values))

@app.route('/export/csv')
def export_csv():
    data = CollecteAgricole.query.all()
    df = pd.DataFrame([{
        'Date': d.date_collecte.strftime('%Y-%m-%d'),
        'Farmer': d.nom_agriculteur,
        'Region': d.region,
        'Crop': d.culture,
        'Area_ha': d.superficie_hectares,
        'Production_kg': d.quantite_produite_kg,
        'Price_FCFA_kg': d.prix_vente_kg,
        'Expenses_FCFA': d.depenses_total,
        'Benefit_FCFA': d.benefice_total(),
        'Yield_kg_ha': d.rendement_hectare(),
        'Season': d.saison,
        'Method': d.methode_culture
    } for d in data])
    
    output = io.StringIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    
    return send_file(io.BytesIO(output.getvalue().encode('utf-8-sig')),
                    mimetype='text/csv',
                    as_attachment=True,
                    download_name=f'agricole_data_{datetime.now().strftime("%Y%m%d")}.csv')

@app.route('/export/excel')
def export_excel():
    return redirect(url_for('export_csv'))

# ==================== LICENSE ROUTES ====================

@app.route('/license')
def license_page():
    """Professional License Information Page"""
    return render_template('license.html', license=LICENSE_INFO)

@app.route('/about')
def about():
    """About the application and developer"""
    return render_template('about.html', license=LICENSE_INFO)

@app.route('/privacy')
def privacy():
    """Privacy Policy Page"""
    return render_template('privacy.html', license=LICENSE_INFO)

# ==================== INITIALIZATION ====================
with app.app_context():
    db.create_all()
    print("\n" + "="*60)
    print("🌾 AgriCollect Cameroon - Professional Edition")
    print("="*60)
    print(f"📜 Licensed to: {LICENSE_INFO['licensee']}")
    print(f"🎓 Matricule: {LICENSE_INFO['matricule']}")
    print(f"🏛️ University: {LICENSE_INFO['university']}")
    print(f"📚 Course: {LICENSE_INFO['course']}")
    print("="*60)
    print("📊 All 10 Regions of Cameroon included:")
    print("   Adamawa, Centre, East, Far North, Littoral")
    print("   North, North West, West, South, South West")
    print("="*60)
    print("🌐 Open: http://localhost:5000")
    print("="*60 + "\n")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

