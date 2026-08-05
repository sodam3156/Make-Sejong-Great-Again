using System;
using System.IO;
using UnityEngine;
using UnityEngine.UIElements;

namespace Tats.Game.UI.Credits
{
    /// <summary>
    /// CreditsScreen.uxml을 그리는 UIDocument에 붙는 얇은 부트스트랩. 서버 연결 없이 뜬다
    /// (docs/23_TITLE_SCREEN_BACKLOG.md T6). 콘텐츠는 <c>Application.streamingAssetsPath</c> 아래
    /// <c>content/credits.json</c>에서 읽는다 — <see cref="CreditsContentStore"/>의 주석대로 실제
    /// server adapter 연동 전까지 쓰는 사본이다. 씬에 이 컴포넌트를 붙이고 시작 화면과 전환을
    /// 연결하는 작업은 Unity Editor가 필요해 사람 몫으로 남긴다 — T1~T5와 같은 이유.
    /// </summary>
    [RequireComponent(typeof(UIDocument))]
    public sealed class CreditsView : MonoBehaviour
    {
        CreditsPresenter _presenter;

        public event Action Back;

        public CreditsPresenter Presenter => _presenter;

        void OnEnable()
        {
            var document = GetComponent<UIDocument>();
            var filePath = Path.Combine(Application.streamingAssetsPath, "content", "credits.json");
            var store = new CreditsContentStore(filePath);
            _presenter = new CreditsPresenter(document.rootVisualElement, store);
            _presenter.Back += OnBack;
        }

        void OnDisable()
        {
            if (_presenter == null)
            {
                return;
            }

            _presenter.Back -= OnBack;
            _presenter.Dispose();
            _presenter = null;
        }

        void OnBack()
        {
            Back?.Invoke();
        }
    }
}
