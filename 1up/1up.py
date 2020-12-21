import ndjson
import glob
import argparse
import sys


class Patient:
    """Prints a report of FHIR resource references for a Patient by id or first and last name"""
    def __init__(self, patient_id=None, first_name=None, last_name=None):
        self.first_name = first_name
        self.last_name = last_name
        self.patient_id = patient_id
        
        # lookup patient ID, or first and alst name
        self.lookup_patient()
        
        # lookup references
        self.lookup_references()

        # lookup references from ecnounters
        self.lookup_encounters()
        
    
    def load_patients(self):
        """Loads Patient file"""
        with open('./data/Patient.ndjson', 'r') as inf:
            patients = ndjson.load(inf)
        return patients
    
    
    def lookup_patient(self):
        """Look up Patients by ID or first and last name"""
        patients = self.load_patients()
        if self.patient_id != None: 
            for patient in patients:
                if patient['id'] == self.patient_id:
                    names = patient['name']        
                    for name in names: # Not needed because [0] is always "official", but keeping it anyway as a check
                        if name['use'] == 'official':
                            self.first_name = name['given'][0]
                            self.last_name = name['family']                            
                            break
                    break            
            
        else:
            if (self.first_name == None) | (self.last_name == None):
                print('You need to provide a patient id, or first name and last name')
                sys.exit(0)
            # lookup patient by name
            for patient in patients:                
                if(patient['name'][0]['given'][0] == self.first_name) & (patient['name'][0]['family'] == self.last_name):
                    self.patient_id = patient['id']
                    break   
    

    def load_resources(self):
        """Loads resource filepaths"""
        return glob.glob('./data/*.ndjson')


    def lookup_references(self):
        """Looks up references to a patient"""
        resource_paths = self.load_resources()
        self.references = {}
        
        for resource_path in resource_paths:
            with open(resource_path, 'r') as inf:
                resources = ndjson.load(inf)
            
            for resource in resources:
                if 'patient' in resource.keys():
                    if resource['patient']['reference'].split('/')[1] == self.patient_id:
                        resource_type = resource['resourceType']
                        if resource_type not in self.references.keys():
                            self.references[resource_type] = 1
                        else:
                            self.references[resource_type] += 1
                elif 'subject' in resource.keys():
                    if resource['subject']['reference'].split('/')[1] == self.patient_id:
                        resource_type = resource['resourceType']
                        if resource_type not in self.references.keys():
                            self.references[resource_type] = 1
                        else:
                            self.references[resource_type] += 1


    def lookup_encounters(self):
        with open('./data/Encounter.ndjson', 'r') as inf:
            encounter_file = ndjson.load(inf)

        for i, encounter in enumerate(encounter_file):
            #print(encounter)

            patient_reference = patient = encounter['subject']['reference'].split('/')[1]
            #print(patient_reference, patient_id)
            if patient_reference == self.patient_id:
                print("cool")

                print(encounter['resourceType'])

                patient = encounter['subject']['reference']

                practitioner = encounter['participant'][0]['individual']['reference']        
                if 'Practitioner' not in self.references.keys():
                    self.references['Practitioner'] = 1
                else:
                    self.references['Practitioner'] += 1

                location = encounter['location'][0]['location']['reference']
                if 'Location' not in self.references.keys():
                    self.references['Location'] = 1
                else:
                    self.references['Location'] += 1

                organization = encounter['serviceProvider']['reference']
                if 'Organization' not in self.references.keys():
                    self.references['Organization'] = 1
                else:
                    self.references['Organization'] += 1


    def print_report(self):
        print("Patient Name:\t", patient.first_name, patient.last_name)
        print("Patient ID:\t", patient.patient_id)
        print("\n")
        print(f"{'RESOURCE_TYPE':25}{'COUNT':<25}")
        print(f"{'-'*30}")
        sorted_references = sorted(patient.references.items(), key=lambda x: x[1], reverse=True)
        for i in sorted_references:
                print(f'{i[0]:25} {i[1]:<25}')




if __name__ == '__main__':    
    parser = argparse.ArgumentParser()    
    parser.add_argument("--patient_id", help="A patient ID")
    parser.add_argument("--first_name", help="A patient's given name")
    parser.add_argument("--last_name", help="A patient's family name")
    args = parser.parse_args()    

    patient = Patient(args.patient_id, args.first_name, args.last_name)
    patient.print_report()
