from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import pytz
from datetime import datetime
from ChatUtils import send_case_update

Base = declarative_base()

class User(Base):
    __tablename__ = 'complaints'

    id = Column(Integer, primary_key=True)
    zone = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    chat_id = Column(String(300), nullable=False)
    address = Column(String(300), nullable=False)
    complaint = Column(String(500), nullable=False)
    crime_type = Column(String(100), nullable=False)
    phone_number = Column(String(15), nullable=False)
    evidence_url = Column(String(100), nullable=False)
    status = Column(String(50), default='In progress')
    crime_subtype = Column(String(100), nullable=False)
    police_station = Column(String(100), nullable=False)
    case_number = Column(String(20), unique=True, nullable=False)
    datetime = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))

    def to_dict(self):
        return {
            "id" : self.id,
            "zone" : self.zone,
            "name" : self.name,
            "chat_id" : self.chat_id,
            "address" : self.address,
            "complaint" : self.complaint,
            "crime" : f"{self.crime_type}, {self.crime_subtype}",
            "phone_number" : self.phone_number,
            "evidence_url" : self.evidence_url,
            "status" : self.status,
            "police_station" : self.police_station,
            "case_number" : self.case_number,
            "datetime" : self.datetime.isoformat() if self.datetime else None
        }        


engine = create_engine('sqlite:///complaint.db', echo=True)
Base.metadata.create_all(engine)

def create_user(case_number, name, phone_number, complaint, address, zone, police_station, crime_type, crime_subtype, evidence_url, chat_id):
    Session = sessionmaker(bind=engine)
    session = Session()
    new_user = User(
        zone=zone,
        name=name,
        address=address,
        chat_id=chat_id,
        complaint=complaint,
        crime_type=crime_type,
        case_number=case_number,
        evidence_url=evidence_url,
        phone_number=phone_number,
        crime_subtype=crime_subtype,
        police_station=police_station,
    )
    session.add(new_user)
    session.commit()
    session.close()

def read_user_by_case_number(case_number):
    Session = sessionmaker(bind=engine)
    session = Session()
    user = session.query(User).filter_by(case_number=case_number).first()
    session.close()
    return user

def get_all_users():
    Session = sessionmaker(bind=engine)
    session = Session()
    users = session.query(User).all()
    session.close()
    return users

def update_case_status(case_number, status):
    Session = sessionmaker(bind=engine)
    session = Session()

    user = session.query(User).filter_by(case_number=case_number).first()

    if user:
        user.status = status
        session.commit() 
        print(f"Case number {case_number} status updated to '{status}'.")
    else:
        print(f"Case number {case_number} not found.")
    
    send_case_update(user.chat_id, case_number, status)
    session.close()

if __name__ == "__main__":
    update_case_status("d2cdb2c8", "In progress")
