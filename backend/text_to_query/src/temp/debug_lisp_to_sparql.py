from pangu.environment.examples.KB.PPODSparqlService import execute_query
from pangu.environment.examples.KB.ppod_environment import lisp_to_sparql

if __name__ == '__main__':
    # lisp = '(AND organization (JOIN hasURL dunes))'
    lisp = '(AND http://xmlns.com/foaf/0.1/Organization (JOIN (R https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#orgManager) (JOIN http://poderopedia.com/vocab/hasURL https://www.fws.gov/refuge/guadalupe-nipomo-dunes)))'
    sparql = lisp_to_sparql(lisp)

    lisp = '(AND http://www.sdsconsortium.org/schemas/sds-okn.owl#BestPracticesAndMandates (AND (JOIN (R https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#mandatedBy) https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#dat_847f7d) (JOIN https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#gmType https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#gmn_7d49e5)))'
    sparql = lisp_to_sparql(lisp)
    rows = execute_query(sparql)

    lisp = '(AND https://raw.githubusercontent.com/adhollander/FSLschemas/main/sustsource.owl#Infrastructure (JOIN https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#hasCapacity 120 MW))'
    sparql = lisp_to_sparql(lisp)
    rows = execute_query(sparql)

    print(sparql)
    print('#results', len(rows), rows[:5])
