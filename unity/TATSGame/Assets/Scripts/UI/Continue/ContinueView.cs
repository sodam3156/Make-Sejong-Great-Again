using System;
using System.IO;
using UnityEngine;
using UnityEngine.UIElements;

namespace Tats.Game.UI.Continue
{
    /// <summary>
    /// ContinueScreen.uxml을 그리는 UIDocument에 붙는 얇은 부트스트랩. 서버 연결 없이 뜬다
    /// (docs/23_TITLE_SCREEN_BACKLOG.md T3). 로컬 저장 슬롯 디렉터리는
    /// <c>Application.persistentDataPath/saves</c>로 고정했다 — 이 경로는 문서 어디에도 정해져 있지
    /// 않은 Unity 쪽 구현 결정이다. GameSave의 필드 계약만 docs/22_TATS_BACKEND_DESIGN_V1.md 10절에
    /// 있고, 저장 위치·파일 이름 규칙은 없다.
    ///
    /// <see cref="Presenter"/>를 공개해 둔 이유: 실제 <c>POST /resume</c> 호출(T3 범위 밖)을 나중에
    /// 붙이는 쪽이 <c>Presenter.ReportResumeSucceeded()</c>/<c>ReportResumeFailed(reason)</c>를
    /// 호출할 수 있어야 한다. 시작 화면과의 실제 화면 전환은 Unity Editor에서 씬을 구성해야 하는
    /// 사람 몫으로 남긴다 — T1·T2와 같은 이유다.
    /// </summary>
    [RequireComponent(typeof(UIDocument))]
    public sealed class ContinueView : MonoBehaviour
    {
        ContinuePresenter _presenter;

        public event Action Back;
        public event Action<GameSaveSlot> ResumeRequested;
        public event Action<GameSaveSlot> Resumed;
        public event Action Quit;

        public ContinuePresenter Presenter => _presenter;

        void OnEnable()
        {
            var document = GetComponent<UIDocument>();
            var slotDirectory = Path.Combine(Application.persistentDataPath, "saves");
            var slotStore = new GameSaveSlotStore(slotDirectory);
            _presenter = new ContinuePresenter(document.rootVisualElement, slotStore);
            _presenter.Back += OnBack;
            _presenter.ResumeRequested += OnResumeRequested;
            _presenter.Resumed += OnResumed;
            _presenter.Quit += OnQuit;
        }

        void OnDisable()
        {
            if (_presenter == null)
            {
                return;
            }

            _presenter.Back -= OnBack;
            _presenter.ResumeRequested -= OnResumeRequested;
            _presenter.Resumed -= OnResumed;
            _presenter.Quit -= OnQuit;
            _presenter.Dispose();
            _presenter = null;
        }

        void OnBack()
        {
            Back?.Invoke();
        }

        void OnResumeRequested(GameSaveSlot slot)
        {
            ResumeRequested?.Invoke(slot);
        }

        void OnResumed(GameSaveSlot slot)
        {
            Resumed?.Invoke(slot);
        }

        void OnQuit()
        {
            Quit?.Invoke();
        }
    }
}
