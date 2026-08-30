// Mock AI responses based on role and query
const roleResponses = {
  student: {
    timetable: {
      text: "Here's your timetable for this week:\n\n**Monday:** Mathematics (9:00), Physics Lab (11:00), CS Theory (2:00)\n**Tuesday:** Data Structures (9:00), Communication Skills (11:00)\n**Wednesday:** DBMS (9:00), Mathematics (11:00), CS Lab (2:00)\n**Thursday:** Physics (9:00), Data Structures Lab (11:00)\n**Friday:** CS Theory (9:00), DBMS Lab (2:00)\n\nWould you like reminders for any of these?",
      sources: ["Student Portal - MUOnline", "Department Schedule 2024"],
      confidence: "high",
    },
    placement: {
      text: "**Recent Placement Updates 🎉**\n\n- **Amazon** visited campus last week — 45 offers made (avg. ₹18 LPA)\n- **Microsoft** drive scheduled for **July 15** — Registration open!\n- **Infosys** and **Wipro** drives in August\n- **Google** PPO extended to 12 students\n\nWould you like to register for any upcoming drives?",
      sources: ["Placement Cell Portal", "T&P Official Announcements"],
      confidence: "high",
    },
    library: {
      text: "**MIT Manipal Library Hours:**\n\n🕗 **Weekdays:** 8:00 AM – 11:00 PM\n🕗 **Saturday:** 9:00 AM – 9:00 PM\n🕗 **Sunday:** 10:00 AM – 6:00 PM\n\n📚 **Digital Library** is available 24/7 via the MULib portal.\n\nYou can also reserve study rooms through the library app!",
      sources: ["MIT Manipal Library Portal"],
      confidence: "high",
    },
    exam: {
      text: "**Upcoming Exam Schedule:**\n\n📅 **Mid-Term Exams:** July 20 – July 28, 2024\n📅 **End-Term Exams:** November 15 – November 30, 2024\n\nHall tickets will be available 5 days before the exam on the student portal. Make sure your attendance is above 75% to be eligible!",
      sources: ["Academic Calendar 2024-25", "Examination Cell"],
      confidence: "high",
    },
  },
  prospective: {
    admission: {
      text: "**Admission Process at MIT Manipal:**\n\n1. **MET (Manipal Entrance Test)** – Online exam held in April/May\n2. **Document Verification** – Original mark sheets, ID proof\n3. **Seat Allotment** – Based on MET rank + preferences\n4. **Fee Payment** – Confirm admission within 3 days of allotment\n\n📌 Applications open **January – March** every year.\n\nWould you like more info on a specific program?",
      sources: ["Admissions Portal - manipal.edu", "MET 2024 Brochure"],
      confidence: "high",
    },
    fee: {
      text: "**Fee Structure (2024–25):**\n\n| Program | Annual Fees |\n|---------|------------|\n| B.Tech (CS/IT) | ₹2,20,000 |\n| B.Tech (EC/ME) | ₹1,95,000 |\n| MBA | ₹3,50,000 |\n| MBBS | ₹12,00,000 |\n\n💡 Scholarships available for merit students (up to 50% waiver)\n\nHostel fees are separate: ₹80,000–₹1,20,000/year",
      sources: ["Fee Structure 2024-25", "Scholarship Guidelines"],
      confidence: "moderate",
    },
    eligibility: {
      text: "**Eligibility Criteria for B.Tech:**\n\n✅ 10+2 with Physics, Chemistry, Mathematics\n✅ Minimum **60% aggregate** in PCM\n✅ Valid **MET / JEE Main** score\n✅ Age: 17–25 years at time of admission\n\nFor NRI students, SAT scores are also accepted.\n\nWant me to check eligibility for a specific program?",
      sources: ["Admissions Eligibility Criteria 2024"],
      confidence: "high",
    },
    campus: {
      text: "**MIT Manipal Campus Highlights:**\n\n🏫 560+ acre green campus\n🔬 State-of-the-art research labs\n🏥 Kasturba Hospital on campus\n🏟️ Sports complex with pool, courts & gym\n🛏️ Air-conditioned hostels\n🍽️ 20+ restaurants and food courts\n\nVirtual campus tours are available at manipal.edu/virtual-tour",
      sources: ["MIT Manipal Official Website", "Campus Facilities Guide"],
      confidence: "high",
    },
  },
  faculty: {
    department: {
      text: "**Department Resources Available:**\n\n📁 Faculty portal: faculty.manipal.edu\n📊 Research publications database\n📋 Student performance analytics\n🔬 Lab booking system (Book via faculty portal)\n📚 Course material upload interface\n\nSemester reports are due by **July 31**. Would you like help with any specific resource?",
      sources: ["Faculty Portal", "Administrative Guidelines 2024"],
      confidence: "high",
    },
    admin: {
      text: "**Administrative Schedule - July 2024:**\n\n📅 Faculty Senate Meeting: July 8, 2:00 PM – Conference Hall A\n📅 Research Committee Review: July 12, 10:00 AM\n📅 Department HOD Meeting: July 18, 3:00 PM\n📅 Semester Academic Audit: July 25\n\nAgendas have been emailed. Please confirm attendance via the faculty portal.",
      sources: ["Administrative Calendar", "HOD Circular #12/2024"],
      confidence: "high",
    },
    research: {
      text: "**Available Research Grants (2024):**\n\n💰 **DST-SERB CRG Grant** – Up to ₹50 Lakhs (Deadline: Aug 15)\n💰 **AICTE Research Promotion Scheme** – Up to ₹20 Lakhs\n💰 **Manipal Internal Grant** – Up to ₹5 Lakhs (Rolling)\n💰 **CSIR Extramural Research** – Open call\n\nContact the Research Office (Ext. 4200) for proposal submission support.",
      sources: ["Research Office Bulletin", "DST Official Portal"],
      confidence: "moderate",
    },
    portal: {
      text: "**Faculty Portal Features:**\n\n🔗 faculty.manipal.edu\n\n- **Course Management:** Upload materials, manage syllabi\n- **Attendance:** Mark & view attendance records\n- **Grading:** Submit grades, view grade distributions\n- **Leave Management:** Apply & track leave requests\n- **Payroll:** View pay slips and tax documents\n\nFor login issues, contact IT Support at ext. 4100.",
      sources: ["Faculty Portal User Guide"],
      confidence: "high",
    },
  },
};

const genericResponses = [
  {
    text: "MIT Manipal (Manipal Institute of Technology) is a premier engineering and technology institution established in 1957. It's ranked among the top private engineering colleges in India, offering programs in Engineering, Management, and Applied Sciences.\n\nWhat specific information would you like to know?",
    sources: ["MIT Manipal Official Website", "NIRF Rankings 2024"],
    confidence: "high",
  },
  {
    text: "I understand your query! Here's what I found based on the MIT Manipal knowledge base:\n\nFor detailed and accurate information, I recommend:\n1. Visiting **manipal.edu** for official data\n2. Contacting the relevant department directly\n3. Checking the **MUOnline portal** if you're a registered student\n\nCould you rephrase your question? I can better assist with specific topics like admissions, courses, placements, or facilities.",
    sources: ["General Knowledge Base"],
    confidence: "moderate",
  },
  {
    text: "Great question! MIT Manipal has a vibrant campus life with 100+ student clubs covering technical, cultural, and sports activities.\n\n**Key highlights:**\n- TechTatva (Annual Tech Fest)\n- Revels (Cultural Festival)\n- MIT ACM Student Chapter\n- E-Cell (Entrepreneurship Cell)\n\nWould you like details on any specific club or event?",
    sources: ["Student Affairs Office", "MITManipal Instagram"],
    confidence: "high",
  },
];

function findBestResponse(message, role) {
  const msg = message.toLowerCase();
  const roleData = roleResponses[role] || roleResponses.student;

  // Check role-specific keywords
  const keywordMap = {
    student: {
      timetable: ["timetable", "schedule", "class", "timing"],
      placement: ["placement", "job", "company", "hire", "recruit", "amazon", "microsoft"],
      library: ["library", "book", "read", "study room"],
      exam: ["exam", "test", "assessment", "hall ticket", "mid-term", "end-term"],
    },
    prospective: {
      admission: ["admission", "apply", "application", "met", "entrance", "jee"],
      fee: ["fee", "cost", "tuition", "scholarship", "payment"],
      eligibility: ["eligible", "eligibility", "criteria", "requirement", "qualify"],
      campus: ["campus", "hostel", "facilities", "tour", "infrastructure"],
    },
    faculty: {
      department: ["department", "resource", "lab", "course material"],
      admin: ["admin", "meeting", "schedule", "senate", "audit"],
      research: ["research", "grant", "funding", "project", "publication"],
      portal: ["portal", "login", "payroll", "attendance", "grade"],
    },
  };

  const roleKeywords = keywordMap[role] || keywordMap.student;
  for (const [key, keywords] of Object.entries(roleKeywords)) {
    if (keywords.some((kw) => msg.includes(kw))) {
      return roleData[key];
    }
  }

  // Generic fallback
  return genericResponses[Math.floor(Math.random() * genericResponses.length)];
}

export function generateAIResponse(message, role) {
  return new Promise((resolve) => {
    const delay = 600 + Math.random() * 800;
    setTimeout(() => {
      const match = findBestResponse(message, role);
      resolve({
        text: match.text,
        sources: match.sources || ["MIT Knowledge Base"],
        citations: (match.sources || ["MIT Knowledge Base"]).map((src) => ({
          source: src,
          snippet: `Passage from ${src} regarding ${message.slice(0, 30)}...`,
          score: 0.88,
        })),
        confidence: match.confidence || "high",
        confidenceType: match.confidence === "high" ? "official_verified" : "community_grounded",
        followups: [
          "What are the official deadlines for this?",
          "How can I contact the department in charge?",
          "Are there alternative guidelines available?",
        ],
      });
    }, delay);
  });
}

