import aiohttp
from pydantic import BaseModel, Field

from typing import Optional, Literal
from pyairtable import Api, Table
from app_settings import (
    AIRTABLE_API_KEY,
    AIRTABLE_BASE_ID,
    AIRTABLE_TABLE_ID,
    BREEZY_HIVEMINDS_EMAIL,
    BREEZY_HIVEMINDS_PASSWORD,
    BREEZY_ROCKETDEVS_EMAIL,
    BREEZY_ROCKETDEVS_PASSWORD,
)

import asyncio


class SignInRequest(BaseModel):
    email: str
    password: str


class SignInResponse(BaseModel):
    access_token: str


class AuthorizedRequest(BaseModel):
    access_token: str


class Company(BaseModel):
    id_: str = Field(alias="_id")
    friendly_id: str


class ListPositionsRequest(BaseModel):
    company_id: str


class Position(BaseModel):
    id_: str = Field(alias="_id")
    friendly_id: str


class ListCandidatesRequest(BaseModel):
    company_id: str
    position_id: str


class CandidateResume(BaseModel):
    id_: str = Field(alias="_id")
    file_name: str
    url: str


class Candidate(BaseModel):
    """
      {
      "_id": "9924435e2ae7",
      "meta_id": "5a49ae354eb4",
      "creation_date": "2025-02-11T13:50:56.559Z",
      "email_address": "fadyeshak94@gmail.com",
      "headline": "Technical Team Lead @ Magic Pay, Nasr City",
      "initial": "F",
      "name": "Fady Eshak",
      "origin": "applied",
      "phone_number": "01221578887",
      "resume": {
        "file_name": "Fady Eshak Fransic-3.pdf",
        "url": "https://app.breezy.hr/public/api/v3/company/6e115ae13ba7/position/e21e057a5421/candidate/9924435e2ae7/resume",
        "error": false,
        "_id": "97bdfb42443a81fe8a98d178effe477f"
      },
      "source": { "id": "linkedin", "name": "LinkedIn" },
      "stage": {
        "id": "applied",
        "name": "Applied",
        "type": { "id": "applied", "name": "Applied", "icon": "user" }
      },
      "tags": [],
      "overall_score": {
        "very_good": [],
        "good": [],
        "neutral": [],
        "poor": [],
        "very_poor": [],
        "scored_count": 0,
        "average_score": null
      },
      "updated_date": "2025-02-11T13:50:56.890Z",
      "bias_status": "applicant"
    }
    """

    id_: str = Field(alias="_id")
    email_address: str
    headline: Optional[str]
    name: Optional[str]
    phone_number: Optional[str]
    # resume: CandidateResume

    def to_airtable(self, source: str):
        return AirtableRecord(
            name=self.name,
            email=self.email_address,
            headline=self.headline,
            phone=self.phone_number,
            source=source,
        )


class GetResumeRequest(BaseModel):
    company_id: str
    position_id: str
    candidate_id: str


class BreezyApi:
    def __init__(self):
        self.headers = {"Content-Type": "application/json"}

    async def sign_in(self, request: SignInRequest):
        """
        curl -H "Content-Type: application/json" \
          -X POST \
          -d '{"email":"jobs@hiveminds.org","password":"RJEAd5$eFJ"}' \
          https://api.breezy.hr/v3/signin
        """
        url = "https://api.breezy.hr/v3/signin"

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json=request.model_dump(), headers=self.headers
            ) as response:
                result = await response.json()
                data = SignInResponse.model_validate(result)
                self.headers["Authorization"] = data.access_token

    async def list_companies(self) -> list[Company]:
        """curl -H "Content-Type: application/json" \
                -H "Authorization: 00000000-0000-0000-0000-000000000000" https://api.breezy.hr/v3/companies"""
        url = "https://api.breezy.hr/v3/companies"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                result = await response.json()
                return [Company.model_validate(company) for company in result]

    async def list_positions(self, request: ListPositionsRequest) -> list[Position]:
        """
        curl -H "Content-Type: application/json" \
                -H "Authorization: 00000000-0000-0000-0000-000000000000"\
                 https://api.breezy.hr/v3/company/000000000000/positions?state=published
        """
        url = f"https://api.breezy.hr/v3/company/{request.company_id}/positions?state=published"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                result = await response.json()
                return [Position.model_validate(position) for position in result]

    async def list_candidates(self, request: ListCandidatesRequest) -> list[Candidate]:
        """
        curl -H "Content-Type: application/json" \
             -H "Authorization: 00000000-0000-0000-0000-000000000000"\
             https://api.breezy.hr/v3/company/000000000000/position/000000000000/candidates?page_size=10&page=1&sort=created
        """
        url = f"https://api.breezy.hr/v3/company/{request.company_id}/position/{request.position_id}/candidates?page_size=1000&page=1&sort=created"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                result = await response.json()
                return [Candidate.model_validate(candidate) for candidate in result]

    async def get_resume(self, request: GetResumeRequest) -> bytes:
        """
        curl -X POST -H "Authorization: 00000000-0000-0000-0000-000000000000"\
             -F'data=@/path/to/file'\
             https://api.breezy.hr/v3/company/000000000000/position/000000000000/candidate/000000000000/resume
        """
        url = f"https://api.breezy.hr/v3/company/{request.company_id}/position/{request.position_id}/candidate/{request.candidate_id}/resume"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                binary_data = await response.read()
                # Convert to base64
                return binary_data


async def fetch_candidates(request: SignInRequest) -> list[Candidate]:
    api = BreezyApi()
    await api.sign_in(request)
    companies = await api.list_companies()
    positions = await asyncio.gather(
        *[api.list_positions(ListPositionsRequest(company_id=c.id_)) for c in companies]
    )
    candidates = await asyncio.gather(
        *[
            api.list_candidates(
                ListCandidatesRequest(company_id=c.id_, position_id=p.id_)
            )
            for c, p_list in zip(companies, positions)
            for p in p_list
        ]
    )
    return [c for c_list in candidates for c in c_list]


class AirtableRecord(BaseModel):
    name: Optional[str]
    email: Optional[str]
    headline: Optional[str]
    phone: Optional[str]
    source: Literal["rocketdevs", "hiveminds", "both"]


class ListAirtableRecord(BaseModel):
    id_: str = Field(alias="id")
    fields: AirtableRecord


def get_table() -> Table:
    api = Api(AIRTABLE_API_KEY)
    return api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_ID)


# records = [ListAirtableRecord.model_validate(r) for r in table.all()]
# print(records)
# table.batch_upsert(key_fields=["email"], replace=False)


async def sync_it():
    rocketdevs_candidates = await fetch_candidates(
        SignInRequest(
            email=BREEZY_ROCKETDEVS_EMAIL, password=BREEZY_ROCKETDEVS_PASSWORD
        )
    )
    hiveminds_candidates = await fetch_candidates(
        SignInRequest(email=BREEZY_HIVEMINDS_EMAIL, password=BREEZY_HIVEMINDS_PASSWORD)
    )
    all_candidates = {
        c.email_address: c.to_airtable("rocketdevs") for c in rocketdevs_candidates
    }
    for c in hiveminds_candidates:
        if c.email_address in all_candidates:
            all_candidates[c.email_address].source = "both"
        else:
            all_candidates[c.email_address] = c.to_airtable("hiveminds")
    print(
        "NumCandidates:",
        len(all_candidates),
        "HM",
        len(all_candidates),
        "RD",
        len(rocketdevs_candidates),
    )
    table = get_table()
    to_insert = [dict(fields=c.model_dump()) for c in all_candidates.values()]
    table.batch_upsert(to_insert, key_fields=["email"], replace=False)


if __name__ == "__main__":
    asyncio.run(sync_it())
