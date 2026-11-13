/* Réception confirmée dans l'espace ; email indépendant en secours. */
(function () {
 'use strict';
 var form=document.getElementById('lead'),ok=document.getElementById('ok');
 if(!form||!ok)return;
 var enCours=false,endpoint='https://menageup-espace.netlify.app/api/demandes/site';
 function requete(url,data,delai){
  var controle=new AbortController(),timer=setTimeout(function(){controle.abort();},delai);
  return fetch(url,{method:'POST',headers:{Accept:'application/json'},body:data,signal:controle.signal,credentials:'omit'})
   .then(function(r){return r.json().then(function(d){return {http:r.status,ok:r.ok,data:d};});})
   .finally(function(){clearTimeout(timer);});
 }
 function secours(fd){
  var mail=new FormData(),choix=[];
  form.querySelectorAll('[name=prestations]').forEach(function(c){if(fd.getAll('prestations').indexOf(c.value)!==-1)choix.push(c.parentElement.textContent.trim());});
  var sujet=('Nouvelle demande · '+fd.get('prenom')+' · '+(fd.get('cp')||'Lieu à préciser')).replace(/[\r\n]+/g,' ').slice(0,180);
  var provenance=form.elements.provenance_declaree;
  mail.append('subject',sujet);mail.append('_subject',sujet);
  mail.append('Client',fd.get('prenom')||'');mail.append('Téléphone',fd.get('tel')||'');
  mail.append('Lieu',fd.get('cp')||'À préciser');mail.append('Prestations',choix.join(', ')||'À préciser');
  mail.append('Précisions',fd.get('precisions')||'Aucune précision ajoutée.');
  var option=provenance?[].slice.call(provenance.options).find(function(o){return o.value===fd.get('provenance_declaree');}):null;
  mail.append('Nous a connus',option&&option.value?option.text:'Non renseigné');
  mail.append('Suivi de la demande','Enregistrement dans l’espace à vérifier : https://menageup-espace.netlify.app/demandes . Cette notification de secours contient la demande complète.');
  if(fd.get('mail')){mail.append('email',fd.get('mail'));mail.append('_replyto',fd.get('mail'));}
  mail.append('from_name','MénageUp · Demande du site');
  mail.append('_template','table');
  mail.append('access_key',form.dataset.emailKey);
  return requete('https://api.web3forms.com/submit',mail,12000).then(function(r){
   if(!r.ok||r.data.success!==true)throw Error('Email non confirmé');
  }).catch(function(){
   mail.delete('access_key');
   return requete('https://formsubmit.co/ajax/menageup@outlook.fr',mail,12000).then(function(r){
    if(!r.ok||(r.data.success!==true&&r.data.success!=='true'))throw Error('Email non confirmé');
   });
  });
 }
 function erreur(message){
  var el=document.getElementById('senderr');
  if(!el){el=document.createElement('p');el.id='senderr';el.className='senderr';el.setAttribute('role','alert');form.appendChild(el);}
  el.textContent=message;
  el.scrollIntoView({behavior:'smooth',block:'center'});
 }
 function reussi(parEmail){
  form.style.display='none';ok.classList.add('show');
  var p=ok.querySelector('.rea');
  if(p)p.textContent=parEmail?'Votre demande nous a été transmise par email. Nous vous recontactons pour préparer votre devis.':'Votre demande a bien été enregistrée. Nous vous recontactons pour préparer votre devis.';
  ok.setAttribute('tabindex','-1');ok.focus({preventScroll:true});ok.scrollIntoView({behavior:'smooth',block:'center'});
 }
 form.addEventListener('submit',async function(e){
  e.preventDefault();
  if(enCours||!form.reportValidity())return;
  var fd=new FormData(form);
  if(fd.get('site_web')){reussi(false);return;}
  enCours=true;
  var boutons=[].slice.call(form.querySelectorAll('[type=submit]'));
  var libelles=boutons.map(function(b){return b.textContent;});
  boutons.forEach(function(b){b.disabled=true;});
  var actif=e.submitter||boutons[0];if(actif)actif.textContent='Envoi en cours…';
  var ancienne=document.getElementById('senderr');if(ancienne)ancienne.remove();
  try {
   var r=await requete(endpoint,fd,18000);
   if(r.ok&&r.data.ok===true){reussi(false);return;}
   // Les erreurs de saisie et limites ne sont pas contournées par un autre canal.
   if(r.http>=400&&r.http<500){erreur(r.data.message||'Vérifiez les informations et réessayez.');return;}
   throw Error('Réception non confirmée');
  } catch (_) {
   try {await secours(fd);reussi(true);}
   catch (_e) {erreur('Nous ne pouvons pas confirmer la réception. Vos informations sont conservées ici : réessayez, ou appelez-nous au 06 48 30 49 65.');}
  } finally {
   enCours=false;boutons.forEach(function(b,i){b.disabled=false;b.textContent=libelles[i];});
  }
 });
})();
