from datetime import datetime
from sqlalchemy import CheckConstraint, UniqueConstraint, Index,
from sqlalchemy.sql import func
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.associationproxy import association_proxy

db = SQLAlchemy()


class Company(db.Model):
    __tablename__ = "companies"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    industry = db.Column(db.String(80), nullable=False)
    join_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    services = db.relationship("Service", back_populates="company", cascade="all, delete-orphan")
    email = db.Column(db.String, unique=True, nullable=False)

    def __repr__(self):
        return f'<Company {self.username}>'

# => maakt tabel met naam Company in database,
# kolom1: id => bestaat uit een getal en wordt gebruikt als identificatie 
# kolom2: username => string met max lengte = 80, moet uniek zijn => geen dubbele usernames, en nullable = False => mag niet leeg zijn voor een user
# elke instantie van Company => 1 rij 

class Service(db.Model):
    __tablename__ = "services"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False) # als bedrijf weg dan moet services erdoor ook weg
    company = db.relationship("Company", back_populates="services")
    offer_or_need = db.Column(db.Boolean, nullable=False, default=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text()) #db.Text() gebruiken ipv bv db.String(1000) als beschrijvingen echt lang kunnen zijn 
    active = db.Column(db.Boolean, nullable=False, default=True)
    deals_offered = db.relationship("Deal", back_populates="service_offered", foreign_keys="Deal.service_offered_id")
    deals_needed = db.relationship("Deal", back_populates="service_needed", foreign_keys="Deal.service_needed_id")

    def __repr__(self):
        kind = "offer" if self.offer_or_need else "need"
        return f"<Service {self.id} {kind} {self.title} ({self.company.username})>"


class Deal(db.Model): 
    __tablename__ = "deals"
    id = db.Column(db.Integer, primary_key=True)
    service_offered_id = db.Column(db.Integer, db.ForeignKey("services.id", ondelete="RESTRICT"), nullable=False) # service kan niet verwijderd worden als de service in een deal zit
    service_needed_id = db.Column(db.Integer, db.ForeignKey("services.id", ondelete="RESTRICT"), nullable=False)
    service_offered = db.relationship("Service", back_populates="deals_offered", foreign_keys=[service_offered_id]) # geen cascade want veranderingen in deals of services mag de ander niet beinvloeden 
    service_needed = db.relationship("Service", back_populates="deals_needed", foreign_keys=[service_needed_id])
    offering_company = association_proxy("service_offered", "company") # via deze proxies worden de betrokken partijen en hun emails aan het contract gelinkt
    needing_company  = association_proxy("service_needed",  "company") # zie tegenhangers bij class Contract
    offering_company_email = association_proxy("offering_company", "email")
    needing_company_email  = association_proxy("needing_company", "email")
    contracts = db.relationship("Contract", back_populates="deal", cascade="all, delete-orphan")
    reviews = db.relationship("Review", back_populates="deal_a")
    # status moet er nog bij

    __table_args__ = CheckConstraint("service_offered_id <> service_needed_id", name="distinct_services")

    def __repr__(self):
        return f"<Deal {self.id} offered={self.service_offered_id} needed={self.service_needed_id}>"
    

#probleem met upgraden van contract en review, migration file al gemaakt 
class Contract(db.Model):
    __tablename__ = "contracts"
    id = db.Column(db.Integer, primary_key=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('deals.id', ondelete="CASCADE"), nullable=False)
    deal = db.relationship("Deal", back_populates="contracts")
    offering_company = association_proxy("deal", "offering_company") # linken van betrokken bedrijven aan een contract
    needing_company  = association_proxy("deal", "needing_company") # beter zo dan extra kolommen?
    offering_company_email = association_proxy("deal", "offering_company_email") # linken van hun emails aan het contract
    needing_company_email  = association_proxy("deal", "needing_company_email")
    doc_name = db.Column(db.String(40), nullable=False) # eventueel de exacte datum en tijd als default waarde 
    doc_path = db.Column(db.String(520), nullable=False) # 520 => sommige tijdelijke (beveiligde) bestanden kunnen een pad of URL hebben dat tegen de 500 tekens in lengte kan zijn, een string gebruiken om het pad op te slaan is belangrijk voor schaalbaarheid
                                                        # het programma automatisch het juiste pad laten toekennen lijkt mij vrij belangrijk, hoe?
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime) # er moet niet per se een einddatum zijn (later: mss werken met perpetuals)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow) #nuttig?
    # obligations = db.Column(db.Text(), nullable=False) => nodig? want contract is het document waarvoor we het adres en naam hebben opgeslaan


class Review(db.Model): 
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('deals.id', ondelete="SET NULL"), nullable=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("companies.id", ondelete="SET NULL"), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    rating = db.Column(db.Integer, nullable=False) 
    comment = db.Column(db.Text()) # mag NULL hebben volgens mij
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reviewer = db.relationship("Company", foreign_keys([reviewer_id]), back_populates = "reviews_written")
    reviewee = db.relationship("Company", foreign_keys([reviewee_id]), back_populates = "reviews_received")
    deal_a = db.relationship("Deal", back_populates="reviews")

# to do:
    # index werking implementeren waar nodig
    # __repr__ instellen
    
